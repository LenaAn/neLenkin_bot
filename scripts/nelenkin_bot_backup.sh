#!/bin/bash
# put it in /usr/local/bin/nelenkin_club_backup.sh
# and add running it to crontab

# Docker container with Postgres. I take snapshots of this Postgres
CONTAINER_NAME=bot_postgres
DB_NAME=nelenkin_club
DB_USER=postgres

# How to store snapshot on AWS
DATE=$(date +%F_%H_%M_%S)
BACKUP_NAME=$DATE.sql.gz
BACKUP_DIR=/var/backups/nelenkin_bot
BACKUP_PATH=$BACKUP_DIR/$BACKUP_NAME

# Cloudfare bucket
# The bucket is private and accessed via Access Token
# Access token is configured on the machine with `aws configure`
R2_BUCKET=nelenkin-bot-backups
R2_ENDPOINT=https://d40843b9f118eda9d6249336a5b175a6.r2.cloudflarestorage.com

# Dump the DB inside docker and compress
docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_PATH"

# Upload backup to Cloudflare R2 bucket
aws s3 cp "$BACKUP_PATH" "s3://$R2_BUCKET/$BACKUP_NAME" \
    --endpoint-url "$R2_ENDPOINT" \
    --region auto

# Delete local backups older than 30 days
find "$BACKUP_DIR" -type f -name '*.sql.gz' -mtime +30 -delete
