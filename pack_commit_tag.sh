#!/bin/bash
DEFAULT_STREAM=6.4.300
while getopts hgts:m:p:v: o
do case "$o" in
  h)
  echo "Usage example: pack_and_commit.sh -p ~/git/nlps-profiles-dev/GM_INFO_3.0/ -s 6.4.200 -m 'ZPP-123: fixes some profile problems'"
  echo "This script will modify the version, create a zip profile pack, add and commit locally all changes, tag, and push the commit and the tag to remote git repository"
  echo "-p                path to the local git repository folder "
  echo "-m                commit message to use. It MUST incude a ZPP, ZPNLPS, PTNCS or PTDD jira number"
  echo "-s                NLPS stream"
  echo "-g                git only. It will not tag in svn. If not set it will tag in svn as well"
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
  g)
    GIT_ONLY="true"
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
	STREAM=${DEFAULT_STREAM}
	echo "Missing nlps-stream parameter: Assuming ${STREAM}. Use -s <stream> to tag for a different stream"
fi
if [ -z "${MSG}" ]; then
	echo "missing commit-message: Cannot continue. Use -m '<message>' to specify the commit message"
	exit -1
fi
if [[ ! "${MSG}" =~ ((NLPS)|(ZPP)|(PTNCS)|(ZPNLPS)|(PTDD)|(ZPNLU)|(PTNLU))-[0-9]+ ]] ;  then
	echo "The commit message must include a ZPP, NLPS, ZPNLPS, PTNCS, PTDD or PTNLU jira number: Cannot continue";
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
# change version
cp $PROFILE_FILE $PROFILE_FILE.bak
if [[ `grep \"VERSION\" $PROFILE_FILE|wc -l` == 0 ]]; then
    echo Added version  ${VER}
	(
		echo "{" 
		echo "	\"VERSION\": \"$VER\","
		tail -n +2 $PROFILE_FILE.bak
    ) > $PROFILE_FILE
else
	sed "s/\"VERSION\" *: *\"[^\"]*\",/\"VERSION\": \"$VER\",/" $PROFILE_FILE.bak > $PROFILE_FILE
	echo Changed version to ${VER}
fi
rm $PROFILE_FILE.bak

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
echo "\"since_nlps_stream\":\"${STREAM}\","
echo "\"comment\":\"${MSG}\","
echo "\"last_modified_by\":\"`git config user.email` `git config user.name`\","
echo "\"url\":\"https://git.labs.nuance.com/nlps-profiles-dev/${PRJ}/raw/${VER}/${ZIP_FILE}\""
echo "}"
) > $MANIFEST_FILE
cat $MANIFEST_FILE
# zipping
rm $ZIP_FILE

set -x
zip -r $ZIP_FILE . -i nlu/\* profiles/\* prompts/\* providers/\* synonyms/\* -x "**/src/*"
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Zip command did not return successfully.  MANUAL RESOLUTION REQUIRED!"
	exit -1
fi

if [ -n "${TEST_ONLY}" ]; then
	echo "Profile packed. There will be no commits or tagging."
	exit 0
fi

set -x
#fetch
git fetch --tags
# commit
git add .
git commit -m "${VER}: ${MSG}"
git push
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Unsuccessful git push. Likely your branch diverged. MANUAL RESOLUTION REQUIRED! Please rebase, resolve conflicts, and run this script again."
	exit -1
fi

# tag version and push tag
set -x
git tag -f ${VER}
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Failed to tag locally. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi
set -x
git push origin ${VER}
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Failed push version tag. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi

# tag to qualify, delete to qualify and push
set -x
git tag -f to-qualify/${STREAM}
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Failed tag to-qualify locally. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi
# deletes remote to-qualify tag
set -x
git push origin :refs/tags/to-qualify/${STREAM}
{ set +x; } 2>/dev/null
# push to-qualify tag
git push origin to-qualify/${STREAM}
if [ $? -ne 0 ]; then
	echo "Failed push to-qualify tag. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi
set -x
git fetch --tags
{ set +x; } 2>/dev/null
if [ $? -ne 0 ]; then
	echo "Failed fetch. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi
DIFF_TAG=`git diff ${VER} to-qualify/${STREAM} | wc -l`
if [ "${DIFF_TAG}" -ne 0 ]; then
	echo "Somebody else tagged concurently to-qualify. MANUAL RESOLUTION REQUIRED!"
	exit -1
fi

echo "==========================================="
echo "What happened:"
echo "TAGGED WITH:"
git tag --contains HEAD
echo "COMMIT:"
git log -1
echo "==========================================="

# also in svn
if [ -z "$GIT_ONLY" ]; then
	set -x
	svn delete https://mobi-svn01.nuance.com/svn/nlps/ps-profiles/tags/to-qualify/$STREAM/$ZIP_FILE -m "delete to replace tag"
	svn import $ZIP_FILE https://mobi-svn01.nuance.com/svn/nlps/ps-profiles/tags/to-qualify/$STREAM/$ZIP_FILE -m "${VER}: svn is a deprecated location, instead use https://git.labs.nuance.com/nlps-profiles-dev/scripts/raw/to-qualify/${STREAM}/${ZIP_FILE} : ${MSG}"
	{ set +x; } 2>/dev/null
	if [ $? -ne 0 ]; then
		echo "Tagging or retagging in svn failed. MANUAL RESOLUTION REQUIRED!"
		exit -1
	fi
fi
cd ${CRT_DIR}
