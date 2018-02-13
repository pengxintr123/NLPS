#!/bin/bash
while getopts hts:m:p:v: o
do case "$o" in
  h)
  echo "Usage example: pack_and_commit.sh -p ~/git/nlps-profiles-dev/GM_INFO_3.0/ -s 6.4.200 -m 'ZPP-123: fixes some profile problems'"
  echo "This script will modify the version, create a zip profile pack, add and commit locally all changes, tag, and push the commit and the tag to remote git repository"
  echo "-p                path to the local git repository folder "
  echo "-m                commit message to use. It MUST incude a ZPP, ZPNLPS, PTNCS, ZPNLU, ZPACC or PTDD jira number"
  echo "-s                NLPS stream for which to release to QA"
  echo "-t                test only. The zip file is created but there is no committing or tagging"
  echo "-h                help"
  echo ""
  exit 0;
  ;;
  s)
    STREAM="${OPTARG//[\"\']/ }"
  ;;
  m)
    MSG="${OPTARG//[\"\']/ }"
  ;;
  p)
    PROJECT_DIR="${OPTARG//[\"\']/ }"
  ;;
  v)
    VER="${OPTARG//[\"\']/ }"
  ;;
  t)
    TEST_ONLY="true"
  ;;
esac
done;
if [ -z "${PROJECT_DIR}" ]; then
PROJECT_DIR=${PWD}
echo "Missing project parameter: Assuming ${PROJECT_DIR}. Use -p to specify full path to profile git project to use"
fi
if [ -z "${STREAM}" ]; then
echo "Missing nlps-stream parameter. THIS VERSION WILL NOT BE RELEASED TO QA!(Use -s <stream> if needed)"
fi
if [ -z "${MSG}" ]; then
echo "missing commit-message: Cannot continue. Use -m '<message>' to specify the commit message"
exit -1
fi
if [[ ! "${MSG}" =~ ((NLPS)|(ZPP)|(PTNCS)|(ZPNLPS)|(PTDD)|(ZPNLU)|(ZPACC)|(PTNLU))-[0-9]+ ]] ;  then
echo "The commit message must include a ZPP, NLPS, ZPNLPS, PTNCS, PTDD, ZPNLU, ZPACC or PTNLU jira number: Cannot continue";
exit -1
fi

if [ -z "$VER" ]; then
VER=`date +%Y%m%d%H%M`
fi

CRT_DIR=`pwd`
cd ${PROJECT_DIR}
PROFILE_FILE=`ls -1 $PWD/profiles/*.json`

if [ -z "$PROFILE_FILE" ]; then
echo "Could not find a profile file in $PWD/profiles/. Are you in the correct folder?"
exit -1
fi
# erase version if there
cp $PROFILE_FILE $PROFILE_FILE.bak
if [[ `grep \"VERSION\" $PROFILE_FILE|wc -l` != 0 ]]; then
    sed "s/\"VERSION\" *: *\"[^\"]*\",//" $PROFILE_FILE.bak > $PROFILE_FILE
# erase version
cp $PROFILE_FILE $PROFILE_FILE.bak
fi
if [[ `grep \"VERSION\" $PROFILE_FILE|wc -l` == 0 ]]; then
    echo Added version  ${VER}
(
echo "{" 
echo "\"VERSION\": \"$VER\","
tail -n +2 $PROFILE_FILE.bak
    ) > $PROFILE_FILE
fi

PRJ=$(basename ${PROFILE_FILE})
PRJ="${PRJ%.*}"
MANIFEST_FILE=profiles/${PRJ}.manifest
ZIP_FILE=${PRJ}.zip

# generate manifest
echo "Generating manifest in ${MANIFEST_FILE}"
(
echo "{"
echo "\"version\":\"${VER}\","
echo "\"last_modified\":\"`date`\","
if [[ ! -z "${STREAM}" ]]; then
echo "\"since_nlps_stream\":\"${STREAM}\","
fi
echo "\"comment\":\"${MSG}\","
echo "\"last_modified_by\":\"`git config user.email` `git config user.name`\","
echo "\"url\":\"https://git.labs.nuance.com/nlps-profiles-dev/${PRJ}/raw/${VER}/${ZIP_FILE}\""
echo "}"
) > $MANIFEST_FILE
cat $MANIFEST_FILE
# zipping
rm $ZIP_FILE

set -x
zip -r $ZIP_FILE . -i nlu/\* profiles/\* prompts/\* providers/\* synonyms/\* -x "**/src/*" -x "**/*.bak"
{ set +x; } 2>/dev/null
rm ${MANIFEST_FILE}
# no longer modify the profile file!
mv $PROFILE_FILE.bak $PROFILE_FILE
if [ $? -ne 0 ]; then
echo "Zip command did not return successfully.  MANUAL RESOLUTION REQUIRED!"
exit -1
fi

if [ -n "${TEST_ONLY}" ]; then
echo "Profile packed. There will be no commits or tagging."
cd ${CRT_DIR}
exit 0
fi

set -x
#fetch
git fetch --tags
# commit
git add .
git commit -m "${VER}: ${MSG}"
git push
if [ $? -ne 0 ]; then
echo "Unsuccessful git push. Likely your branch diverged. MANUAL RESOLUTION REQUIRED! Please rebase, resolve conflicts, and run this script again."
exit -1
fi

# tag version and push tag
set -x
git tag -f ${VER}
if [ $? -ne 0 ]; then
echo "Failed to tag locally. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
set -x
git push origin ${VER}
if [ $? -ne 0 ]; then
echo "Failed push version tag. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
if [[ ! -z "${STREAM}" ]]; then
# tag to qualify, delete to qualify and push
set -x
git tag -f to-qualify/${STREAM}
if [ $? -ne 0 ]; then
echo "Failed tag to-qualify locally. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
# deletes remote to-qualify tag
set -x
git push origin :refs/tags/to-qualify/${STREAM}
# push to-qualify tag
git push origin to-qualify/${STREAM}
if [ $? -ne 0 ]; then
echo "Failed push to-qualify tag. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
set -x
git fetch --tags
if [ $? -ne 0 ]; then
echo "Failed fetch. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
DIFF_TAG=`git diff ${VER} to-qualify/${STREAM} | wc -l`
if [ "${DIFF_TAG}" -ne 0 ]; then
echo "Somebody else tagged concurently to-qualify. MANUAL RESOLUTION REQUIRED!"
exit -1
fi
fi
{ set +x; } 2>/dev/null
echo "============================================================================================"
echo "What happened:"
echo "    TAGGED WITH:"
git tag --contains HEAD
echo "    COMMIT:"
git log -1
echo "============================================================================================"
if [[ -z "${STREAM}" ]]; then
echo "    NOTE: Version ${VER} was NOT release to QA!"
else
echo "    WARNING: Version ${VER} tagged as to-qualify/${STREAM}!"
echo "    WARNING: This pushes the version to QA, and in some cases directly customer-facing."
echo "    WARNING: If you did not intended that, you MUST delete the tag to-qualify/${STREAM}."
fi
echo "============================================================================================"
cd ${CRT_DIR}

