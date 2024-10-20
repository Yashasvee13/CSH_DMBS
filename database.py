#!/usr/bin/env python3
import psycopg2

#####################################################
##  Database Connection
#####################################################

'''
Connect to the database using the connection string
'''
def openConnection():
    userid = "postgres"           
    passwd = ""  
    myHost = "localhost"           
    myDatabase = "Assignment2"

    conn = None
    try:
        #
        conn = psycopg2.connect(
            database=myDatabase,  
            user=userid,      
            password=passwd,  
            host=myHost       
        )
    except psycopg2.Error as sqle:
        
        print("psycopg2.Error : " + sqle.pgerror)
    
    return conn


'''
Validate staff based on username and password
'''
def checkLogin(login, password):

    conn = openConnection()
    cursor = conn.cursor()

    # Call stored procedure
    cursor.callproc('check_admin_login_procedure', (login, password))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result if result else None


'''
List all the associated admissions records in the database by staff
'''
def findAdmissionsByAdmin(login):
 
    conn = openConnection()
    cursor = conn.cursor()

    # Call stored procedure
    cursor.callproc('find_admissions_by_admin_procedure', (login,))
    
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    admissions_list = []
    for row in results:
        
        admissions_list.append({
            'admission_id': row[0] if row[0] is not None else "",
            'admission_type': row[1] if row[1] is not None else "",
            'admission_department': row[2] if row[2] is not None else "",
            'discharge_date': row[3] if row[3] is not None else "",
            'fee': row[4] if row[4] is not None else "",
            'patient': row[5] if row[5] is not None else "",
            'condition': row[6] if row[6] is not None else ""
        })

    return admissions_list


'''
Find a list of admissions based on the searchString provided as parameter
See assignment description for search specification
'''
def findAdmissionsByCriteria(searchString):

    conn = openConnection()
    cursor = conn.cursor()

    query = """
        SELECT a.AdmissionID, at.AdmissionTypeName, d.DeptName, 
               TO_CHAR(a.DischargeDate, 'DD-MM-YYYY') AS discharge_date, -- Format date in SQL
               a.Fee, 
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

    
    searchPattern = f"%{searchString}%"

    
    cursor.execute(query, (searchString, searchPattern, searchPattern, searchPattern, searchPattern))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        print(f"No results found for search string: {searchString}")

   
    admissions_list = [
        {
            'admission_id': row[0] if row[0] else "",
            'admission_type': row[1] if row[1] else "",
            'admission_department': row[2] if row[2] else "",
            'discharge_date': row[3] if row[3] else "",  
            'fee': row[4] if row[4] else "",
            'patient': row[5] if row[5] else "",
            'condition': row[6] if row[6] else ""
        }
        for row in results
    ]

    return admissions_list

'''
Add a new addmission 
'''
def addAdmission(type, department, patient, condition, admin):

    try:
        conn = openConnection()
        cursor = conn.cursor()

        
        cursor.execute(
            "SELECT AdmissionTypeID FROM AdmissionType WHERE LOWER(AdmissionTypeName) = LOWER(%s)", 
            (type,)
        )
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{type}' not found.")
        
        
        cursor.execute(
            "SELECT DeptId FROM Department WHERE LOWER(DeptName) = LOWER(%s)", 
            (department,)
        )
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department}' not found.")

        patient_id = patient
        print(patient_id)

        
        query = """
            INSERT INTO Admission (AdmissionType, Department, Patient, Administrator, Condition)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING AdmissionID
        """
        
       
        cursor.execute(query, (admission_type_id, department_id, patient_id, admin, condition))
        
        
        admission_id = cursor.fetchone()[0]

        
        conn.commit()

        
        cursor.close()
        conn.close()

        return admission_id is not None 

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()  
        return False

'''
Update an existing admission
'''
def updateAdmission(id, type, department, dischargeDate, fee, patient, condition):

    try:
        conn = openConnection()
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT AdmissionTypeID FROM AdmissionType WHERE LOWER(AdmissionTypeName) = LOWER(%s)", (type,))
        admission_type_id = cursor.fetchone()
        if not admission_type_id:
            raise ValueError(f"Admission type '{type}' not found.")
        
        
        cursor.execute("SELECT DeptId FROM Department WHERE LOWER(DeptName) = LOWER(%s)", (department,))
        department_id = cursor.fetchone()
        if not department_id:
            raise ValueError(f"Department '{department}' not found.")
        
       
        cursor.execute("SELECT PatientId FROM Patient WHERE LOWER(PatientID) = LOWER(%s)", (patient,))
        patient_id = cursor.fetchone()
        if not patient_id:
            raise ValueError(f"Patient '{patient}' not found.")

       
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
            dischargeDate if dischargeDate else None, 
            fee if fee else None, 
            patient_id, 
            condition if condition else None,
            id
        ))

        
        conn.commit()

        
        cursor.close()
        conn.close()

        return True  

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()  
        return False