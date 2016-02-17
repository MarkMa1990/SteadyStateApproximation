# -*- coding: utf-8 -*-
"""
Created on Oct 14, 2015

@author: Inom Mirzaev

"""


from __future__ import division
from scipy.optimize import fsolve 
from multiprocessing import Pool


import numpy as np
import scipy.linalg as lin
import time


start = time.time()

# Minimum and maximum floc sizes
x0 = 0
x1 = 1

# Post-fragmentation density distribution
def gam( y , x , x0 = x0 ):
    
    out = 6*y * ( x - y )  / (x**3)
    
    if type(x) == np.ndarray or type(y) == np.ndarray:        
        out[y>x] = 0

    return out 
    


#Aggregation rate
def ka(x,y, x1=x1):
    
    out = ( x ** ( 1/3 ) + y ** ( 1/3 ) ) **3      

    return out

def q(x):
    
    return x + 1
    
def g(x):

    return x + 1
    
        
   #Removal rate    
def rem(x):

     return x
     
#Fragmentation rate

def kf(x):

    return x
    
# Initializes uniform partition of (x0, x1) and approximate operator F_n

N=100

#delta x
dx = ( x1 - x0 ) / N

#Uniform partition into smaller frames
nu = x0 + np.arange(N+1) * dx

#Aggregation in
Ain = np.zeros( ( N , N ) )

#Aggregation out
Aout = np.zeros( ( N , N ) )

#Fragmentation in
Fin = np.zeros( ( N , N ) )

#Fragmentation out
Fout = np.zeros( N )


for mm in range( N ):

    for nn in range( N ):
        
        if mm>nn:
        
            Ain[mm,nn] = 0.5 * dx * ka( nu[mm] , nu[nn+1] )
        
        if mm + nn < N-1 :
            
            Aout[mm, nn] = dx * ka( nu[mm+1] , nu[nn+1] )
                
        if nn > mm :
        
            Fin[mm, nn] = dx * gam( nu[mm+1], nu[nn+1] ) * kf( nu[nn+1] )


Fout = - np.diag( 0.5 * kf( nu[range( 1 , N + 1 ) ] ) ) 

#Removal operator
Removal =  - np.diag( rem( nu[range( 1 , N + 1 )] ) )

#Growth operator
Growth = np.zeros( ( N , N ) )

#Renewal operator
Renewal = np.zeros( ( N , N ) )
Renewal[0,:] = Renewal[0,:] + q( nu[range( 1 , N+1 ) ] )

for jj in range(N-1):
    Growth[jj,jj] = -g( nu[jj+1] ) / dx
    Growth[jj+1,jj] = g( nu[jj+1] ) / dx
    
Growth[N-1, N-1] = -g( nu[N] ) / dx


part = 10

x_ = np.linspace(15, 0, 15*4*part, endpoint=False).tolist()
x_.sort()
y_ = np.linspace(1, 0, part, endpoint=False).tolist()
y_.sort()
z_ = np.linspace(5, 0, 5* part, endpoint=False).tolist()
z_.sort()

x, y, z = np.meshgrid(x_, y_, z_, indexing='ij')


x = np.ravel( x )
y = np.ravel( y )
z = np.ravel( z )

myarray = np.array( [ x , y , z ] ).T



def region_plots(nn,  Growth=Growth, Renewal=Renewal, Removal=Removal, 
                 myarray = myarray, Fout=Fout, Fin=Fin, Ain=Ain, Aout=Aout):
    
    pos_sol = 0
    eigs2=0

    An = myarray[nn , 0]*Renewal + myarray[nn , 1]*Growth  + myarray[nn, 2]*Removal - np.diag( Fout ) + Fin
    
    
    #The right hand side of the evolution equation
    def root_finding( y ,  An=An , Aout=Aout , Ain=Ain):
        
        a = np.zeros_like(y)

        a [ range( 1 , len( a ) ) ] = y [ range( len( y ) - 1 ) ]    

        out = np.dot( Ain * lin.toeplitz( np.zeros_like(y) , a).T - ( Aout.T * y ).T + An , y ) 
          
        return out

    #Exact Jacobian of the RHS 
    def exact_jacobian(y, An=An, Aout=Aout, Ain=Ain):

        a = np.zeros_like(y)

        a [ range( 1 , len( a ) ) ] = y [ range( len( y ) - 1 ) ] 

        out = An - ( Aout.T * y ).T - np.diag( np.dot(Aout , y) ) + 2*Ain * lin.toeplitz( np.zeros_like(y) , a).T

        return out    

    
    for mm in range( 10 ):

        if mm < 5:    
            seed = 10 * (mm + 1) * np.ones(N)            
            
        else:
            seed = 10* ( mm - 4 ) * np.arange(N)
            
        sol = fsolve( root_finding ,  seed , fprime = exact_jacobian , xtol = 1e-8 , full_output=1 )

        if sol[2]==1 and np.linalg.norm( sol[0] ) > 1 and np.all( sol[0] > 0 ):
            pos_sol = 1
            eigs2 = np.max(  np.real ( np.linalg.eig(  exact_jacobian( sol[0] ) )[0] ) )  

            break
        
    return ( myarray[nn , 0] , myarray[nn , 1] , myarray[nn, 2] , pos_sol , eigs2 )
    
    
if __name__ == '__main__':
    pool = Pool(processes = 12 )
    ey_nana = range( len( myarray) )
    result = pool.map( region_plots , ey_nana )
    
    output = np.asarray(result)
    
    #output = output[ np.nonzero( output[: , 3 ] ) ]
    
    
    fname = 'data_' + time.strftime("%Y_%m_%d_%H_%M", time.gmtime())    
    np.save(fname , output )
    
    

end = time.time()


print "Elapsed time " + str( round( (end - start) / 60 , 1)  ) + " minutes"


