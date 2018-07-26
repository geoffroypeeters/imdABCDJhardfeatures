#!/usr/bin/env bash
 
TMP_DIR='./tmp/'
MPG123="/opt/local/bin/mpg123"
IMD="./_mac/imdABCDJ-1.1.0"
IMDHF="./imdABCDJhardfeatures.py"

FILE_NAME=$1
FILE_WAV=$TMP_DIR`basename $1`.wav
FILE_XML=$TMP_DIR`basename $1`.xml
FILE_JSON=$TMP_DIR`basename $1`.json

echo $FILE_NAME
echo $FILE_WAV_22K_MONO
echo $FILE_XML

"$MPG123" -w "$FILE_WAV" "$FILE_NAME"

echo "$IMD" -i "$FILE_WAV" -o "$FILE_XML"
"$IMD" -i "$FILE_WAV" -o "$FILE_XML"

"$IMDHF" -a "$FILE_WAV" -x "$FILE_XML" -o "$FILE_JSON" --tmpdir "$TMP_DIR"
