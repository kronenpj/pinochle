This is a network-based, distributed card game engine. It will initially
support 4-person pinochle game but I will attempt to make it modular and
generic where possible.

The application accepts several arguments, all of which are optional:
```
usage: pinochle.py [-h] [-d DATABASE] [-f OUTPUTFILE] [-j {html.j2,latex.j2,text.j2}]
                   [-p {1,2,3,T,G,E,t,g,e}] [-q]
                   [-r {NONE,RANDOM,ABCD,DCBA,none,random,abcd,dcba}]
                   [-s SEED] [-v] [-V]

A network-based pinochle card game for four people.

optional arguments:
  -h, --help            show this help message and exit
  -d DATABASE, --database DATABASE
                        Choose the source database file
  -f OUTPUTFILE, --outputfile OUTPUTFILE
                        Specify an output file name. Supply a single dash (-) to output the exam to
                        stdout. If this option is omitted, a filename will be generated.
  -j {html.j2,latex.j2,text.j2}, --jinjafile {html.j2,latex.j2,text.j2}
                        Choose the Jinja template file for the exam
  -p {1,2,3,T,G,E,t,g,e}, --pool {1,2,3,T,G,E,t,g,e}
                        Choose the question pool for the exam, based on the order in which it appears
                        or the first character of the p_name column.
  -q, --no-question-shuffle
                        Disable question shuffling
  -r {NONE,RANDOM,ABCD,DCBA,none,random,abcd,dcba}, --randtype {NONE,RANDOM,ABCD,DCBA,TEMP1-1,none,random,abcd,dcba}
                        Choose the response randomization algorithm
  -s SEED, --seed SEED  Specify a test number to re-create
  -v                    Turn on verbose debugging output
  -V                    View application version information and exit
```

