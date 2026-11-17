cheat:for
# basic loop
for i in 1 2 3 4 5 6 7 8 9 10
do
  echo $i
done
# loop ls command results
for var in `ls -alF`
do
  echo $var
done
# loop over all the JPG files in the current directory
for jpg_file in *.jpg
do
  echo $jpg_file
done
# loop specified number of times
for i in `seq 1 10`
do
  echo $i
done
# same as above, but as one-liner
for i in `seq 1 10`; do echo $i; done
# loop specified number of times: the C/C++ style
for ((i=1;i<=10;++i))
do
  echo $i
done
# loop specified number of times: the brace expansion
for i in {1..10}
do
  echo $i
done
 tldr:for
# for
# Perform a command several times.
# More information: <https://www.gnu.org/software/bash/manual/bash.html#Looping-Constructs>.
# Execute the given commands for each of the specified items:
for variable in item1 item2 ...; do echo "Loop is executed"; done
# Iterate over a given range of numbers:
for variable in {from..to..step}; do echo "Loop is executed"; done
# Iterate over a given list of files:
for variable in path/to/file1 path/to/file2 ...; do echo "Loop is executed"; done
# Iterate over a given list of directories:
for variable in path/to/directory1/ path/to/directory2/ ...; do echo "Loop is executed"; done
# Perform a given command in every directory:
for variable in */; do (cd "$variable" || continue; echo "Loop is executed") done
