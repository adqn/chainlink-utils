#!/bin/bash
echo -e "Enter available port for adapter to listen on: \c "
read -e port

usedport=`netstat -ntl | grep $port`

while [ "$usedport" != "" ]
do
	echo -e "Port in use, please select another port: \c"
	read -e port
	usedport=`netstat -ntl | grep $port`
done

echo -e "Enter name to assign adapter in the Docker container (using dashes instead of spaces): \c "
read -e dockername

echo -e "Enter name of adapter to run (adaptername-adapter): \c"
read -e adapter

#if [ "$adapter" == "defi-pulse-adapter" ]
#then
#	
#fi

echo -e "Enter API key if required by adapter (leave blank if none): \c"
read -e apikey

echo -e "Was the adapter container pulled from public.ecr.aws/chainlink? (Y/N): \c"
read -e containerpulled

echo -e "Are there required environment variables? (Y/N): \c"
read -e reqenv

while [ "$reqenv" == "Y" ] || [ "$reqenv" == "y" ]
do
	echo -e "Enter the variable name: \c"
	read -e varname

	echo -e "Enter the value for $varname: \c"
	read -e varvalue

	envvalue="$varname=$varvalue"
	envcommand="$envcommand -e $envvalue"
	echo $envvalue >> ~/adapters/envs/.$adapter
	
	echo -e "Add another environment variable? (Y/N): \c"
	read -e reqenv
done
	

if [ "$containerpulled" == "Y" ] || [ $containerpulled == "y" ]
then 
	if [ "$apikey" != "" ] 
	then
		docker run --name=$dockername -d -p $port:8080 -e API_KEY=$apikey $envcommand public.ecr.aws/chainlink/adapters/$adapter:latest
	else
		docker run --name=$dockername -d -p $port:8080 $envcommand  public.ecr.aws/chainlink/adapters/$adapter:latest
	fi
else
	if [ "$apikey" != "" ] 
	then
		cd ~/adapters && docker-compose -f docker-compose.generated.yaml run --name=$dockername -d -p $port:8080 -e API_KEY=$apikey $envcommand $adapter
	else
		cd ~/adapters && docker-compose -f docker-compose.generated.yaml run --name=$dockername -d -p $port:8080 $envcommand $adapter
	fi
fi
