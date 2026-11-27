package ro.dj88bid.freeform;
import java.util.Arrays;
class BoundsTest {public static void main(String[] args){
 if(!Arrays.equals(Bounds.of(0,0,1280,720,55,15,40,70),new int[]{704,108,1216,612}))throw new AssertionError();
 if(!Arrays.equals(Bounds.of(10,20,1000,500,0,0,100,100),new int[]{10,20,1010,520}))throw new AssertionError();
 int[][] invalid={{90,0,20,20},{0,90,20,20},{0,0,19,20},{-1,0,50,50},{0,0,50,101}};
 for(int[] a:invalid){try{Bounds.of(0,0,1280,720,a[0],a[1],a[2],a[3]);throw new AssertionError();}catch(IllegalArgumentException expected){}}
 System.out.println("7 bounds assertions passed");}}