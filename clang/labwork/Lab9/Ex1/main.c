#include <stdio.h>

int getInt(char message[]);

/*Λεκτική περιγραφή:
Πάρε αριθμό μικρών μπουκαλιών.
Πάρε αριθμό μεγάλων μπουκαλιών.
Υπολόγισε τον συνολικό αριθμό μπουκαλιών και την αρχική τιμή.
Αν η τιμή είναι μεγαλύτερη από 600 ευρώ, εφάρμοσε 24% έκπτωση και ανανέωσε την τιμή.
Αν η τιμή είναι μεταξύ 300 και 600 ευρώ ή ο αριθμός μπουκαλιών είναι μεγαλύτερος του 1000, εφάρμοσε 12% έκπτωση και ανανέωσε την τιμή.
Εμφάνισε την τιμή.*/

int main(int argc, char *argv[]) {
	printf("Exercise 1 program running:\n");
	
	int smallBottles=getInt("Enter number of small bottles: ");
	int largeBottles=getInt("Enter number of large bottles: ");
	int numOfBottles=smallBottles+largeBottles;
	
	float totalPrice=smallBottles*0.08+largeBottles*0.2;
	
	if(numOfBottles>600){
		printf("Your total price in euros is: %.2f", totalPrice);
		totalPrice=totalPrice-(totalPrice*0.24);
		printf("\nYou have a 24 percent discount. Your final price in euros is: %.2f", totalPrice);
	}
	else if(300<totalPrice<600||numOfBottles>1000){
		printf("Your total price in euros is: %.2f", totalPrice);
		totalPrice=totalPrice-(totalPrice*0.12);
		printf("\nYou have a 12 percent discount. Your total price in euros is: %.2f", totalPrice);
	}
	else printf("Your total price in euros is: %.2f", totalPrice);
	return 0;
	
}

int getInt(char message[]){
	printf(message);
	int num;
	scanf("%d", &num);
	return num;
}

