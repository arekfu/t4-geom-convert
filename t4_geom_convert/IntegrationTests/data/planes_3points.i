Test for double-sheet cones with 0 as sheet param
c cells
    1 1 -1.0 446 -1000
    2 2 -1.0 -446 -1000
 1000 0 1000

c surfaces
c   1  P 0 0 20 1 0 20 0 1 20  $ a complicated way to specify the z=20 plane
 446 2 p   -44 187 54.5 44 187 54.5 0 76 104
 1000  SO  1000

m1
              13027        -1.0
m2
              13027        -1.0
mode n
c
c IMPORTANCES
c
imp:n   1 1 0
*TR2 0.0 0.0 0.0 22.5 67.5 90.0 112.5 22.5 90.0 90.0 90.0 0.0