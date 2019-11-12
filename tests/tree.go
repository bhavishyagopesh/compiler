// Tree in Go
package main;
 
import "fmt";
 
var Tree; struct {
	key; int ;
	Left; *Tree;
	Right; *Tree;
};
 


func Println(s; str);
var nil; *Tree;
 
func main() {
	var parent; = &Tree;
	parent.key = 1 ;;
	parent.Left = nil ;;
	parent.Right = nil ;;
	

	var lchild; = &Tree;
	lchild.key = 2 ;;
	lchild.Left = nil ;;
	lchild.Right = nil ;;
	
	var rchild; = &Tree;
	rchild.key = 3 ;;
	rchild.Left = nil ;;
	rchild.Right = nil ;;

	
    Println(parent);;
};
