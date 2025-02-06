#!/usr/bin/env bash
# USAGE: ./download_readthedocs.sh <url>
# USAGE: ./download_readthedocs.sh https://python.langchain.com/en/latest/


# Check if url is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <url>"
    exit 1
fi


url=$1

# The wget command you provided is used to download files from the internet. Here is a breakdown of what each part of the command does:

# wget: The command-line utility used for downloading files from the web.

# -r: This option stands for "recursive download," which means that wget will download not only the specified URL but also any files linked from that page, up to a certain depth.

# -A.html: This option specifies the file acceptance criteria. In this case, it tells wget to only download files with the .html extension.

# -P rtdocs: This option sets the directory prefix for saved files. wget will download the files into the rtdocs directory.

# https://python.langchain.com/en/latest/: This is the URL of the website from which the files will be downloaded.

# So, the entire command will recursively download all HTML files from the specified URL and save them in the rtdocs directory.

set -x

mkdir rtdocs || true

# shellcheck disable=SC2086
wget -r -A.html -P rtdocs ${url}


# Here's a breakdown of the aria2 command options used:

# -x 10: This sets the number of multiple connections per server to 10, allowing for faster downloads.
# -j 10: This sets the number of parallel downloads to 10.
# --dir=rtdocs: This sets the directory where the downloaded files will be saved to rtdocs.
# --accept=.html: This specifies that only files with the .html extension should be downloaded.
# --recursive: This enables recursive downloading of the files from the specified URL.
# This aria2 command should achieve the same result as the wget command you provided.

# aria2c -x 10 -j 10 --dir=rtdocs --accept=.html --recursive https://pytorch.org/docs/stable/index.html
# aria2c -x 10 -j 10 --dir=rtdocs --accept=.html --recursive ${url}
