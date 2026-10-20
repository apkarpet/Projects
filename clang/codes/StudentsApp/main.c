#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_NAME_LENGTH 50
#define MAX_TEAM_SIZE 18

typedef struct {
    char name[MAX_NAME_LENGTH];
    char lastname[MAX_NAME_LENGTH];
    int id;
} Student;

typedef struct {
    Student students[MAX_TEAM_SIZE];
    int count;
} Team;

void createTeam(Team *team);
void printStudent(Student student);
void printTeam(Team *team);
void loadTeamFromFile(Team *team);
void searchStudentById(Team *team);
void searchStudentByName(Team *team);
void saveTeamToFile(Team *team);
void displayMenu();

int main() {
    Team team = {0};
    int choice;
    
    while (1) {
        displayMenu();
        
        if (scanf("%d", &choice) != 1) {
            printf("Invalid input. Please enter a number.\n");
            continue;
        }
        
        switch (choice) {
            case 1:
                createTeam(&team);
                break;
            case 2:
                printTeam(&team);
                break;
            case 3:
                loadTeamFromFile(&team);
                break;
            case 4:
                searchStudentById(&team);
                break;
            case 5:
                searchStudentByName(&team);
                break;
            case 6:
                saveTeamToFile(&team);
                break;
            case 7:
                printf("Exiting program.\n");
                return 0;
            default:
                printf("Invalid choice. Please try again.\n");
        }
    }
    
    return 0;
}


void createTeam(Team *team) {
    int numStudents;
    
    team->count = 0;
    
    printf("How many students do you want to add to the team? (max %d): ", MAX_TEAM_SIZE);
    while (1) {
        if (scanf("%d", &numStudents) != 1 || 
            numStudents <= 0 || 
            numStudents > MAX_TEAM_SIZE) {
            printf("Invalid number. Please enter a number between 1 and %d: ", MAX_TEAM_SIZE);
    
            continue;
        }
        break;
    }
    
    for (int i = 0; i < numStudents; i++) {
        printf("\nEnter details for Student %d:\n", i + 1);
        
        printf("Enter first name: ");
        scanf("%49s", team->students[i].name);

        printf("Enter last name: ");
        scanf("%49s", team->students[i].lastname);
        
        while (1) {
            printf("Enter 5-digit ID: ");
            if (scanf("%d", &team->students[i].id) == 1 && 
                team->students[i].id >= 10000 && team->students[i].id <= 99999) {
                break;
            }
            printf("Invalid ID. Must be a 5-digit number.\n");
        }
        
    }
    
    team->count = numStudents;
    
    printf("\nTeam of %d students created successfully.\n", numStudents);
}

void printStudent(Student student) {
    printf("Name: %s %s\n", student.name, student.lastname);
    printf("ID: %d\n", student.id);
}

void printTeam(Team *team) {
    if (team->count == 0) {
        printf("Team is empty.\n");
        return;
    }
    
    printf("\n--- Team: ---\n");
    for (int i = 0; i < team->count; i++) {
        printf("\nStudent %d:\n", i + 1);
        printStudent(team->students[i]);
    }
}

void loadTeamFromFile(Team *team) {
    FILE *file;
    char filename[100];
    
    printf("Enter filename to load team from: ");
    scanf("%99s", filename);
    
    file = fopen(filename, "r");
    if (file == NULL) {
        printf("Error opening file.\n");
        return;
    }
    
    team->count = 0;
    
    while (team->count < MAX_TEAM_SIZE && 
           fscanf(file, "%49s %49s %d", 
                  team->students[team->count].name, 
                  team->students[team->count].lastname, 
                  &team->students[team->count].id) == 3) {
        team->count++;
    }
    
    fclose(file);
    printf("Team loaded. %d students added.\n", team->count);
}

void searchStudentById(Team *team) {
    int searchId;
    bool found = false;
    
    printf("Enter student ID to search: ");
    scanf("%d", &searchId);
	    
    for (int i = 0; i < team->count; i++) {
        if (team->students[i].id == searchId) {
            printf("Student found:\n");
            printStudent(team->students[i]);
            found = true;
            break;
        }
    }
    
    if (!found) {
        printf("No student found with ID %d.\n", searchId);
    }
}

void searchStudentByName(Team *team) {
    char searchName[MAX_NAME_LENGTH];
    bool found = false;
    
    printf("Enter name or lastname to search: ");
    scanf("%49s", searchName);
    
    for (int i = 0; i < team->count; i++) {
        if (strcasecmp(team->students[i].name, searchName) == 0 || 
            strcasecmp(team->students[i].lastname, searchName) == 0) {
            if (!found) {
                printf("Matching students:\n");
            }
            printStudent(team->students[i]);
            found = true;
        }
    }
    
    if (!found) {
        printf("No students found with name/lastname %s.\n", searchName);
    }
}

void saveTeamToFile(Team *team) {
    FILE *file;
    char filename[100];
    
    if (team->count == 0) {
        printf("Team is empty. Nothing to save.\n");
        return;
    }
    
    printf("Enter filename to save team: ");
    scanf("%99s", filename);
    
    file = fopen(filename, "w");
    if (file == NULL) {
        printf("Error opening file.\n");
        return;
    }
    
    for (int i = 0; i < team->count; i++) {
        fprintf(file, "%s %s %d\n", 
                team->students[i].name, 
                team->students[i].lastname, 
                team->students[i].id);
    }
    
    fclose(file);
    printf("Team saved successfully.\n");
}

void displayMenu() {
    printf("\n--- Student Management System ---\n");
    printf("1. Create a new team of students\n");
    printf("2. Print team roster\n");
    printf("3. Load team from file\n");
    printf("4. Search student by ID\n");
    printf("5. Search student by name/lastname\n");
    printf("6. Save team to file\n");
    printf("7. Exit\n");
    printf("Enter your choice: ");
}


