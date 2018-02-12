filename=$1
make &&
bin/codegen "test/$filename.ir" 2>&1 >/dev/null &&
mkdir -p "bnf/" &&
nasm -f elf32 "bnf/$filename.s" &&
gcc -m32 "bnf/$filename.o" -o "bnf/a.out" &&
bnf/a.out &&
rm "bnf/a.out" "bnf/$filename.o"