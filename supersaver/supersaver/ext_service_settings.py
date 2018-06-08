# AWS Settings:

# Important:
# If you change any of the AWS_S3_BUCKET_AUTH or AWS_S3_MAX_AGE_SECONDS settings, you will need to run below command
# before the changes will be applied to existing media files.
# ./manage.py s3_sync_meta path.to.your.storage

# The region to connect to when storing files.
AWS_REGION = "ap-southeast-2"

# The AWS access key used to access the storage buckets.
AWS_ACCESS_KEY_ID = "<Placeholder>"
# The AWS secret access key used to access the storage buckets.
AWS_SECRET_ACCESS_KEY = "<Placeholder>"
# The S3 bucket used to store uploaded files.
AWS_S3_BUCKET_NAME = "<Placeholder>"
# A prefix to add to the start of all uploaded files.
AWS_S3_KEY_PREFIX = ""

# Whether to enable querystring authentication for uploaded files.
# Note:
# The default settings assume that user-uploaded file are private. This means that they are only accessible via
# S3 authenticated URLs, which is bad for browser caching.
# To make user-uploaded files public, and enable aggressive caching, we turn off S3 bucket auth and let s3 hold
# uploaded files longer.
# Important:
# Do NOT upload file contains sensitive data.
# If you change any of the AWS_S3_BUCKET_AUTH or AWS_S3_MAX_AGE_SECONDS settings, you will need to run below command
# before the changes will be applied to existing media files.
# ./manage.py s3_sync_meta path.to.your.storage
AWS_S3_BUCKET_AUTH = False
# The expire time used to access uploaded files.
AWS_S3_MAX_AGE_SECONDS = 60*60*24*365  # 1 year.

# The S3 bucket used to store static files.
AWS_S3_BUCKET_NAME_STATIC = ""
# A prefix to add to the start of all static files.
AWS_S3_KEY_PREFIX_STATIC = ""
# The expire time used to access static files.
AWS_S3_MAX_AGE_SECONDS_STATIC = 60*60*24*365  # 1 year.

# Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won’t attempt authentication.
EMAIL_HOST_USER = "<Placeholder>"

# Password to use for the SMTP server defined in EMAIL_HOST. This setting is used in conjunction with EMAIL_HOST_USER
# when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication.
EMAIL_HOST_PASSWORD = "<Placeholder>"