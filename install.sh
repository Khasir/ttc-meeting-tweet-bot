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
