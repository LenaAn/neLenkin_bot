#!/bin/bash
# put it in /usr/local/bin/nelenkin_club_backup.sh
# and add running it to crontab

# Digital Ocean machine where backup is stored
DO_USER=root
DO_HOST=digital_ocean
DO_BACKUP_DIR=/var/backups/nelenkin_bot
DO_KEY_PATH=/home/ec2-user/.ssh/do_key

# Docker container with Postgres. I take snapshots of this Postgres
CONTAINER_NAME=bot_postgres
DB_NAME=nelenkin_club
DB_USER=postgres

# How to store snapshot on AWS
DATE=$(date +%F)
BACKUP_NAME=$DATE.sql.gz
BACKUP_TMP=/tmp/$BACKUP_NAME

# Dump the DB inside docker and compress
docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_TMP"

# Copy to DO
scp -i "$DO_KEY_PATH" "$BACKUP_TMP" $DO_USER@$DO_HOST:$DO_BACKUP_DIR/

# Remove local temp file
rm "$BACKUP_TMP"

# Trigger rotation on DO
ssh -i "$DO_KEY_PATH" $DO_USER@$DO_HOST "find \$DO_BACKUP_DIR -type f -name '*.sql.gz' -mtime +30 -delete"
