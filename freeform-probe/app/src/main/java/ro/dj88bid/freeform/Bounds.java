package ro.dj88bid.freeform;
final class Bounds {
 static int[] of(int left,int top,int width,int height,int x,int y,int w,int h) {
  if(width<1||height<1||x<0||y<0||w<20||h<20||x>100-w||y>100-h) throw new IllegalArgumentException("Invalid bounds");
  int[] r={left+(int)((long)width*x/100),top+(int)((long)height*y/100),left+(int)((long)width*(x+w)/100),top+(int)((long)height*(y+h)/100)};
  if(r[2]<=r[0]||r[3]<=r[1]) throw new IllegalArgumentException("Empty bounds");return r;
 }
}