#!/bin/bash
echo "Behold, fuse mounting S3"
mkdir -p ${FUSE_MOUNT_POINT}
/usr/bin/s3fs ${S3_BUCKET_PATH} ${FUSE_MOUNT_POINT} -o iam_role=viz_brayns-ecsTaskRole -o ecs
ls /sbo/data/project

echo Passed arguments: "$*"
eval "$*"
