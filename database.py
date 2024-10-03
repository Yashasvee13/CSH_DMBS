#!/usr/bin/env python3
import psycopg2
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
    conn = openConnection()
    cursor = conn.cursor()
    query = "SELECT username, firstname, lastname, email FROM administrator WHERE username = %s AND password = %s"
    cursor.execute(query, (login, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print(result)
    return result if result else None




'''
List all the associated admissions records in the database by staff
'''
def findAdmissionsByAdmin(login):
    conn = openConnection()
    cursor = conn.cursor()
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
    cursor.execute(query, (login,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert results to a list of dictionaries for easier access in templates
    admissions_list = []
    for row in results:
        admissions_list.append({
            'admission_id': row[0],
            'admission_type': row[1],
            'admission_department': row[2],
            'discharge_date': row[3],
            'fee': row[4],
            'patient': row[5],
            'condition': row[6]
        })

    return admissions_list



'''
Find a list of admissions based on the searchString provided as parameter
See assignment description for search specification
'''


# def findAdmissionsByCriteria(searchString):
#     conn = openConnection()
#     cursor = conn.cursor()

#     # SQL query to find admissions based on the search criteria
#     query = """
#         SELECT a.AdmissionID, at.AdmissionTypeName, d.DeptName, 
#                a.DischargeDate, a.Fee, 
#                p.FirstName || ' ' || p.LastName AS PatientName, 
#                a.Condition
#         FROM Admission a
#         JOIN AdmissionType at ON a.AdmissionType = at.AdmissionTypeID
#         JOIN Department d ON a.Department = d.DeptId
#         JOIN Patient p ON a.Patient = p.PatientID
#         WHERE (
#             LOWER(at.AdmissionTypeName) LIKE LOWER(%s) OR
#             LOWER(d.DeptName) LIKE LOWER(%s) OR
#             LOWER(p.FirstName || ' ' || p.LastName) LIKE LOWER(%s) OR
#             LOWER(a.Condition) LIKE LOWER(%s)
#         )
#         AND (a.DischargeDate IS NULL OR a.DischargeDate > CURRENT_DATE - INTERVAL '2 years')
#         ORDER BY 
#             COALESCE(a.DischargeDate, '9999-12-31') ASC,
#             PatientName ASC
#     """

#     # Prepare the search pattern for wildcard matching
#     searchPattern = f"%{searchString}%"
    
#     # Execute the query with the search pattern applied to all relevant fields
#     cursor.execute(query, (searchPattern,) * 4)
#     results = cursor.fetchall()
    
#     cursor.close()
#     conn.close()
#     print(results)
#     # Convert results to a list of dictionaries for easier access in templates
#     admissions_list = []
#     for row in results:
#         admissions_list.append({
#             'admission_id': row[0],
#             'admission_type': row[1],
#             'admission_department': row[2],
#             'discharge_date': row[3],
#             'fee': row[4],
#             'patient': row[5],
#             'condition': row[6]
#         })

#     return admissions_list

# # def findAdmissionsByCriteria(searchString):

# #     return

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
            LOWER(at.AdmissionTypeName) LIKE LOWER(%s) OR
            LOWER(d.DeptName) LIKE LOWER(%s) OR
            LOWER(p.FirstName || ' ' || p.LastName) LIKE LOWER(%s) OR
            LOWER(a.Condition) LIKE LOWER(%s)
        )
        AND (a.DischargeDate IS NULL OR a.DischargeDate > CURRENT_DATE - INTERVAL '2 years')
        ORDER BY 
            a.DischargeDate IS NOT NULL,
            COALESCE(a.DischargeDate, '9999-12-31') ASC,
            PatientName ASC
    """

    # Prepare the search pattern for wildcard matching
    searchPattern = f"%{searchString}%"
    
    # Execute the query with the search pattern applied to all relevant fields
    cursor.execute(query, (searchPattern,) * 4)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not results:
        print(f"No results found for search string: {searchString}")

    # Convert results to a list of dictionaries for easier access in templates
    admissions_list = []
    for row in results:
        admissions_list.append({
            'admission_id': row[0],
            'admission_type': row[1],
            'admission_department': row[2],
            'discharge_date': row[3],
            'fee': row[4],
            'patient': row[5],
            'condition': row[6]
        })

    return admissions_list



'''
Add a new addmission 
'''
# def addAdmission(type, department, patient, condition, admin):
#     conn = openConnection()
#     cursor = conn.cursor()
#     query = """
#         INSERT INTO admission (admissiontype, department, patient, condition, admin_username)
#         VALUES (%s, %s, %s, %s, %s)
#         RETURNING id
#     """
#     cursor.execute(query, (type, department, patient, condition, admin))
#     admission_id = cursor.fetchone()[0]
#     conn.commit()
#     cursor.close()
#     conn.close()
#     return admission_id

def addAdmission(admission_type_name, department_name, patient_name, condition, admin_username):
    try:
        conn = openConnection()
        cursor = conn.cursor()

        # Retrieve AdmissionTypeID based on AdmissionTypeName (case-insensitive)
        cursor.execute(
            "SELECT AdmissionTypeID FROM AdmissionType WHERE LOWER(AdmissionTypeName) = LOWER(%s)", 
            (admission_type_name,)
        )
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{admission_type_name}' not found.")
        
        # Retrieve DeptId based on DeptName (case-insensitive)
        cursor.execute(
            "SELECT DeptId FROM Department WHERE LOWER(DeptName) = LOWER(%s)", 
            (department_name,)
        )
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department_name}' not found.")
        
        # # Retrieve PatientID based on Patient's full name (case-insensitive)
        # cursor.execute(
        #     "SELECT PatientID FROM Patient WHERE LOWER(patientid) = LOWER(%s)", 
        #     (patient_id,)
        # )
        patient_id = patient_name
        print(patient_id)
        # if not patient_id:
        #     raise ValueError(f"Patient '{patient_name}' not found.")

        # Insert new admission record
        query = """
            INSERT INTO Admission (AdmissionType, Department, Patient, Administrator, Condition)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING AdmissionID
        """
        
        cursor.execute(query, (admission_type_id, department_id, patient_id, admin_username, condition))
        
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


# def addAdmission(type, department, patient, condition, admin):
    
#     return


'''
Update an existing admission
'''
def updateAdmission(admission_id, admission_type_name, department_name, discharge_date, fee, patient_name, condition):
    try:
        conn = openConnection()
        cursor = conn.cursor()

        # Retrieve AdmissionTypeID based on AdmissionTypeName
        cursor.execute("SELECT AdmissionTypeID FROM AdmissionType WHERE AdmissionTypeName = %s", (admission_type_name,))
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{admission_type_name}' not found.")
        
        # Retrieve DeptId based on DeptName
        cursor.execute("SELECT DeptId FROM Department WHERE DeptName = %s", (department_name,))
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department_name}' not found.")
        
        # Retrieve PatientID based on Patient's full name
        cursor.execute("SELECT PatientID FROM Patient WHERE CONCAT(FirstName, ' ', LastName) = %s", (patient_name,))
        patient_id = cursor.fetchone()
        if not patient_id:
            raise ValueError(f"Patient '{patient_name}' not found.")
        
        

        # Update the admission record
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
        
        cursor.execute(query, (
            admission_type_id[0], 
            department_id[0], 
            discharge_date if discharge_date else None, 
            fee if fee else None, 
            patient_id[0], 
            condition if condition else None,
            admission_id
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
