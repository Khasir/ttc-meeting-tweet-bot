#!/usr/bin/env bash

# TODO test this script

# Install PostgreSQL
# From https://www.postgresql.org/download/linux/ubuntu/
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
apt-get update
apt-get -y install postgresql

# Set up postgres login
PASSWORD=pass
echo "CREATE DATABASE meetings;" | psql
echo "CREATE USER ubuntu WITH PASSWORD '$PASSWORD';" | psql
echo "GRANT ALL PRIVILEGES ON DATABASE meetings TO ubuntu;" | psql
echo "\c meetings; GRANT ALL ON SCHEMA public TO ubuntu;" | psql

# Postgres password
echo "# hostname:port:database:username:password" > psql-pgpass.key
echo "*:*:*:ubuntu:$PASSWORD" >> psql-pgpass.key

# Set up Python env
mkdir env
cd env
python3 -m venv .
source bin/activate
cd ..
pip install --upgrade pip wheel
pip install -r requirements.txt

# Set up Twitter credential file
cat << EOF >> twitter-key.key
{
    "consumer_key": "abcde",
    "consumer_key_secret": "abcdefghi",
    "access_token": "1234-abcde",
    "access_token_secret": "abcdefghi"
}
EOF
echo "Insert your Twitter consumer and access keys into twitter-key.txt."
