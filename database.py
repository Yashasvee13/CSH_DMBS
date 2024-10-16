#!/usr/bin/env python3
import psycopg2
from datetime import datetime
from database_connection import openConnection

#####################################################
##  Database Connection
#####################################################

'''
Connect to the database using the connection string
'''

'''
Validate staff based on username and password
'''


def checkLogin(login, password):
    """
    Check if the provided login credentials are valid.

    This function queries the database to verify if the given username (case-insensitive)
    and password combination exists in the administrator table.

    Args:
        login (str): The username to check.
        password (str): The password to verify.

    Returns:
        tuple or None: A tuple containing user information if credentials are valid,
                       None otherwise.
    """
    conn = openConnection()  # Establish database connection
    cursor = conn.cursor()

    # SQL query with case-insensitive username comparison
    query = """
        SELECT username, firstname, lastname, email 
        FROM administrator 
        WHERE LOWER(username) = LOWER(%s) AND password = %s
    """

    # Execute the query with provided login and password
    cursor.execute(query, (login, password))

    # Fetch the first matching result
    result = cursor.fetchone()

    # Close the cursor and database connection
    cursor.close()
    conn.close()

    # Print the result for debugging (consider removing in production)
    print(result)

    # Return the result if found, otherwise return None
    return result if result else None




'''
List all the associated admissions records in the database by staff
'''

def findAdmissionsByAdmin(login):
    """
    Retrieve admissions managed by a specific administrator.

    This function queries the database to fetch admission details for all admissions
    managed by the administrator with the given login.

    Args:
        login (str): The username of the administrator.

    Returns:
        list: A list of dictionaries, each containing details of an admission.
    """
    conn = openConnection()  # Establish database connection
    cursor = conn.cursor()

    # SQL query to fetch admission details
    query = """
        SELECT a.AdmissionID, at.AdmissionTypeName, d.DeptName, 
               a.DischargeDate, a.Fee, 
               p.FirstName || ' ' || p.LastName AS PatientName, 
               a.Condition
        FROM Admission a
        JOIN AdmissionType at ON a.AdmissionType = at.AdmissionTypeID
        JOIN Department d ON a.Department = d.DeptId
        JOIN Patient p ON a.Patient = p.PatientID
        WHERE a.Administrator = %s
        ORDER BY 
            a.DischargeDate IS NULL,
            COALESCE(a.DischargeDate, '9999-12-31') DESC,
            PatientName ASC,
            at.AdmissionTypeName DESC
    """

    # Execute the query with the provided login
    cursor.execute(query, (login,))
    
    # Fetch all results
    results = cursor.fetchall()

    # Close cursor and database connection
    cursor.close()
    conn.close()

    # Convert results to a list of dictionaries for easier access in templates
    admissions_list = []
    for row in results:
        # Format the discharge date to DMY format
        discharge_date = ""
        if row[3] is not None:
            try:
                date_obj = datetime.strptime(str(row[3]), '%Y-%m-%d')
                discharge_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                # If date parsing fails, use the original value
                discharge_date = str(row[3])

        # Create a dictionary for each admission, replacing None with empty string
        admissions_list.append({
            'admission_id': row[0] if row[0] is not None else "",
            'admission_type': row[1] if row[1] is not None else "",
            'admission_department': row[2] if row[2] is not None else "",
            'discharge_date': discharge_date,
            'fee': row[4] if row[4] is not None else "",
            'patient': row[5] if row[5] is not None else "",
            'condition': row[6] if row[6] is not None else ""
        })

    return admissions_list

'''
Find a list of admissions based on the searchString provided as parameter
See assignment description for search specification
'''


from datetime import datetime

def findAdmissionsByCriteria(searchString):
    conn = openConnection()
    cursor = conn.cursor()

    # SQL query to find admissions based on the search criteria
    query = """
        SELECT a.AdmissionID, at.AdmissionTypeName, d.DeptName, 
               a.DischargeDate, a.Fee, 
               p.FirstName || ' ' || p.LastName AS PatientName, 
               a.Condition
        FROM Admission a
        JOIN AdmissionType at ON a.AdmissionType = at.AdmissionTypeID
        JOIN Department d ON a.Department = d.DeptId
        JOIN Patient p ON a.Patient = p.PatientID
        WHERE (
            %s = '' OR  -- Add this condition to handle empty search string
            LOWER(at.AdmissionTypeName) LIKE LOWER(%s) OR
            LOWER(d.DeptName) LIKE LOWER(%s) OR
            LOWER(p.FirstName || ' ' || p.LastName) LIKE LOWER(%s) OR
            LOWER(a.Condition) LIKE LOWER(%s)
        )
        AND (a.DischargeDate IS NULL OR a.DischargeDate > CURRENT_DATE - INTERVAL '2 years')
        ORDER BY 
            a.DischargeDate IS NOT NULL,
            COALESCE(a.DischargeDate, '9999-12-31') ASC,  -- Most recent dates first
            PatientName ASC
    """

    # Prepare the search pattern for wildcard matching
    searchPattern = f"%{searchString}%"
    
    # Execute the query with the search pattern applied to all relevant fields
    cursor.execute(query, (searchString, searchPattern, searchPattern, searchPattern, searchPattern))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not results:
        print(f"No results found for search string: {searchString}")

    # Convert results to a list of dictionaries for easier access in templates
    admissions_list = []
    for row in results:
        # Format the discharge date to DMY format
        discharge_date = ""
        if row[3] is not None:
            try:
                date_obj = datetime.strptime(str(row[3]), '%Y-%m-%d')
                discharge_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                # If date parsing fails, use the original value
                discharge_date = str(row[3])

        # Create a dictionary for each admission, replacing None with empty string
        admissions_list.append({
            'admission_id': row[0] if row[0] is not None else "",
            'admission_type': row[1] if row[1] is not None else "",
            'admission_department': row[2] if row[2] is not None else "",
            'discharge_date': discharge_date,
            'fee': row[4] if row[4] is not None else "",
            'patient': row[5] if row[5] is not None else "",
            'condition': row[6] if row[6] is not None else ""
        })

    return admissions_list


'''
Add a new addmission 
'''

def addAdmission(type, department, patient, condition, admin):
    """
    Add a new admission to the database.

    Args:
        type (str): Name of the admission type.
        department_name (str): Name of the department.
        patient_name (str): Name of the patient.
        condition (str): Medical condition of the patient.
        admin_username (str): Username of the administrator.

    Returns:
        bool: True if admission was added successfully, False otherwise.
    """
    try:
        conn = openConnection()
        cursor = conn.cursor()

        # Retrieve AdmissionTypeID based on AdmissionTypeName (case-insensitive)
        cursor.execute(
            "SELECT AdmissionTypeID FROM AdmissionType WHERE LOWER(AdmissionTypeName) = LOWER(%s)", 
            (type,)
        )
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{type}' not found.")
        
        # Retrieve DeptId based on DeptName (case-insensitive)
        cursor.execute(
            "SELECT DeptId FROM Department WHERE LOWER(DeptName) = LOWER(%s)", 
            (department,)
        )
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department}' not found.")

        patient_id = patient
        print(patient_id)

        # SQL query to insert new admission
        query = """
            INSERT INTO Admission (AdmissionType, Department, Patient, Administrator, Condition)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING AdmissionID
        """
        
        # Execute the insert query
        cursor.execute(query, (admission_type_id, department_id, patient_id, admin, condition))
        
        # Fetch the newly created AdmissionID
        admission_id = cursor.fetchone()[0]

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return admission_id is not None  # Return True if successful

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()  # Rollback in case of error
        return False


'''
Update an existing admission
'''
def updateAdmission(id, type, department, dischargeDate, fee, patient, condition):
    """
    Update an existing admission in the database.

    Args:
        id (int): ID of the admission to update.
        type (str): Name of the admission type.
        department (str): Name of the department.
        dischargeDate (str or None): Discharge date of the patient.
        fee (float or None): Fee charged for the admission.
        patient (str): ID of the patient.
        condition (str or None): Medical condition of the patient.

    Returns:
        bool: True if admission was updated successfully, False otherwise.
    """
    try:
        conn = openConnection()
        cursor = conn.cursor()

        # Retrieve AdmissionTypeID based on AdmissionTypeName
        cursor.execute("SELECT AdmissionTypeID FROM AdmissionType WHERE AdmissionTypeName = %s", (type,))
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{type}' not found.")
        
        # Retrieve DeptId based on DeptName
        cursor.execute("SELECT DeptId FROM Department WHERE DeptName = %s", (department,))
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department}' not found.")

        # SQL query to update the admission record
        query = """
            UPDATE Admission 
            SET 
                AdmissionType = %s,
                Department = %s,
                DischargeDate = %s,
                Fee = %s,
                Patient = %s,
                Condition = %s
            WHERE AdmissionID = %s
        """
        
        # Execute the update query with parameters
        cursor.execute(query, (
            admission_type_id[0], 
            department_id[0], 
            dischargeDate if dischargeDate else None, 
            fee if fee else None, 
            patient, 
            condition if condition else None,
            id
        ))

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return True  # Return True if successful

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()  # Rollback in case of error
        return False