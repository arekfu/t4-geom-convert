Test for line continuation
c a line continuation with an ampersand
    10 0 &
-1000 *fill=2 imp:n=1
c an ampersand at the end of a line comment: &
    1 1 -1.0 -1 U=2
      imp:n=1  $ a line continuation with indentation
c an ampersand in a line comment, &, in the middle
    2 2 -1.0 1 U=2 imp:n=1  $ an ampersand in an inline comment: &
 1000 0 1000 imp:n=0

c surfaces
   1  SO 50
       $ an ampersand in an inline comment: &
 1000  SO  100 $ an ampersand in an inline comment: &

m1
              13027        -1.0
m2
              13027        -1.0
mode n