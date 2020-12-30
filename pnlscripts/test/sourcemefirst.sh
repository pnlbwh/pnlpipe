pushd ../../
if [ ! -f ../../_env.sh ]; then
    echo "Running 'make env' in ../../"
    echo '--------------------------------------------------------------'
    make env
    echo '--------------------------------------------------------------'
    echo "Done, ../../_env.sh is made"
fi
echo 'Now source _env.sh'
echo '--------------------------------------------------------------'
source _env.sh
echo '--------------------------------------------------------------'
popd
for var in $(compgen -v); do export $var; done
