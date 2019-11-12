package main;

import "fmt";
func Println(s; str, j; int);
func len();
func main() {

    var a; [8]int ;
    var twoD; [2][3]int;
    Println("emp:", a);;

    Println("set:", a);;
    Println("get:", a[4]);;

    // Println("len:", len(a));;

    // fmt.Println("dcl:", b);;
    var i,j; = 0,0;
    
    // var j; = 0;
    for i = 0; i < 2; i++; {
        for j= 0; j < 3; j++; {
            twoD[i][j] = i + j ;;
            if i==3
            {
                continue;
            };
            if i>4
            {
                break;
            };
        };
};

};
