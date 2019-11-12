package main;

import "fmt";


func Println(s; str);
func fibonacci (n ; int) (int)
{
	var a, b, t, i ; int;
	a = 0 ;;
	b = 1 ;;


	for i  = 0 ; i < 1 ; i++;
	{
		t = b;;
		b = b + a ;;
		a = t ;;
	};
	return a;
};


func main() {
	Println("Function of 10 is ");;
	Println(fibonacci(10)) ;;
};