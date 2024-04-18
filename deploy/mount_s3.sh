#!/bin/bash
echo "Behold, fuse mounting S3"
mkdir -p ${FUSE_MOUNT_POINT:-/sbo/data/project}
/usr/bin/s3fs ${S3_BUCKET_NAME:-sbo-cell-svc-perf-test } ${FUSE_MOUNT_POINT:-/sbo/data/project} -o iam_role=viz_brayns-ecsTaskRole   -o ecs
ls  /sbo/data/project

echo Passed arguments: "$*"
eval "$*"
