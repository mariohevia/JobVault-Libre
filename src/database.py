import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

class JobDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                company_website TEXT,
                position TEXT NOT NULL,
                status TEXT NOT NULL,
                location TEXT,
                date_applied TEXT,
                contact_name TEXT,
                contact_email TEXT,
                salary_range TEXT,
                job_url TEXT,
                job_description TEXT,
                notes TEXT,
                cv_pdf BLOB,
                cv_text TEXT,
                cover_letter_pdf BLOB,
                cover_letter_text TEXT,
                last_update TEXT
                )""")
    
        self.conn.commit()
    
    def add_job(self, 
            company: str, 
            position: str, 
            status: str,
            company_website: Optional[str] = None,
            location: Optional[str] = None,
            date_applied: Optional[str] = None,
            contact_name: Optional[str] = None,
            contact_email: Optional[str] = None,
            salary_range: Optional[str] = None,
            job_url: Optional[str] = None,
            job_description: Optional[str] = None,
            notes: Optional[str] = None,
            cv_pdf: Optional[bytes] = None,
            cv_text: Optional[str] = None,
            cover_letter_pdf: Optional[bytes] = None,
            cover_letter_text: Optional[str] = None) -> int:
        # TODO: deal with errors in the database.
        """
        Add a new job application to the database.
        
        Args:
            company: Company name (required)
            position: Job position (required)
            status: Application status (required)
            All other parameters are optional
            
        Returns:
            The ID of the newly created job application
        """
        last_update = datetime.now().isoformat()
    
        self.cursor.execute("""
            INSERT INTO job_applications (
                company, company_website, position, status, location,
                date_applied, contact_name, contact_email, salary_range,
                job_url, job_description, notes, cv_pdf, cv_text,
                cover_letter_pdf, cover_letter_text, last_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company, company_website, position, status, location,
            date_applied, contact_name, contact_email, salary_range,
            job_url, job_description, notes, cv_pdf, cv_text,
            cover_letter_pdf, cover_letter_text, last_update))
        
        self.conn.commit()
        return self.cursor.lastrowid
        
    def edit_job(self,
             job_id: int,
             company: Optional[str] = None,
             company_website: Optional[str] = None,
             position: Optional[str] = None,
             status: Optional[str] = None,
             location: Optional[str] = None,
             date_applied: Optional[str] = None,
             contact_name: Optional[str] = None,
             contact_email: Optional[str] = None,
             salary_range: Optional[str] = None,
             job_url: Optional[str] = None,
             job_description: Optional[str] = None,
             notes: Optional[str] = None,
             cv_pdf: Optional[bytes] = None,
             cv_text: Optional[str] = None,
             cover_letter_pdf: Optional[bytes] = None,
             cover_letter_text: Optional[str] = None) -> bool:
        """
        Edit an existing job application. Only updates fields that are provided.
        
        Args:
            job_id: The ID of the job application to edit (required)
            All other parameters are optional - only provided fields will be updated
            
        Returns:
            True if the job was updated, False if job_id doesn't exist
        """
        # Build the UPDATE query dynamically based on provided fields
        fields_to_update = []
        values = []
        
        if company is not None:
            fields_to_update.append("company = ?")
            values.append(company)
        if company_website is not None:
            fields_to_update.append("company_website = ?")
            values.append(company_website)
        if position is not None:
            fields_to_update.append("position = ?")
            values.append(position)
        if status is not None:
            fields_to_update.append("status = ?")
            values.append(status)
        if location is not None:
            fields_to_update.append("location = ?")
            values.append(location)
        if date_applied is not None:
            fields_to_update.append("date_applied = ?")
            values.append(date_applied)
        if contact_name is not None:
            fields_to_update.append("contact_name = ?")
            values.append(contact_name)
        if contact_email is not None:
            fields_to_update.append("contact_email = ?")
            values.append(contact_email)
        if salary_range is not None:
            fields_to_update.append("salary_range = ?")
            values.append(salary_range)
        if job_url is not None:
            fields_to_update.append("job_url = ?")
            values.append(job_url)
        if job_description is not None:
            fields_to_update.append("job_description = ?")
            values.append(job_description)
        if notes is not None:
            fields_to_update.append("notes = ?")
            values.append(notes)
        if cv_pdf is not None:
            fields_to_update.append("cv_pdf = ?")
            values.append(cv_pdf)
        if cv_text is not None:
            fields_to_update.append("cv_text = ?")
            values.append(cv_text)
        if cover_letter_pdf is not None:
            fields_to_update.append("cover_letter_pdf = ?")
            values.append(cover_letter_pdf)
        if cover_letter_text is not None:
            fields_to_update.append("cover_letter_text = ?")
            values.append(cover_letter_text)
        
        # Always update last_update
        fields_to_update.append("last_update = ?")
        values.append(datetime.now().isoformat())
        
        # Add job_id for WHERE clause
        values.append(job_id)
        
        if len(fields_to_update) == 1:  # Only last_update was added
            return False
        
        query = f"""
            UPDATE job_applications
            SET {', '.join(fields_to_update)}
            WHERE id = ?
        """
        
        self.cursor.execute(query, values)
        self.conn.commit()
        
        return self.cursor.rowcount > 0

    def remove_job(self, job_id: int) -> bool:
        """
        Remove a job application from the database.
        
        Args:
            job_id: The ID of the job application to remove
            
        Returns:
            True if the job was deleted, False if job_id doesn't exist
        """
        # TODO: Handle errors better than just print
        # TODO: Consider using a soft delete instead or archive
        try:
            self.cursor.execute(
                "DELETE FROM job_applications WHERE id = ?",
                (job_id,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False

    def get_all_jobs(self) -> List[Tuple]:
        """
        Retrieve all job applications (up to 1000) from the database.
        
        Returns:
            List of tuples containing all job application data
        """
        self.cursor.execute("""
            SELECT id, company, company_website, position, status, location,
                   date_applied, contact_name, contact_email, salary_range,
                   job_url, job_description, notes, cv_text,
                   cover_letter_text, last_update
            FROM job_applications
            ORDER BY last_update DESC
            LIMIT 1000
        """)
        return self.cursor.fetchall()

    def get_cv_pdf(self, job_id: int) -> Optional[bytes]:
        """
        Retrieve the CV PDF for a specific job application.
        
        Args:
            job_id: The ID of the job application
            
        Returns:
            PDF binary data if exists, None otherwise
        """
        self.cursor.execute(
            "SELECT cv_pdf FROM job_applications WHERE id = ?", 
            (job_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None
    
    def get_cover_letter_pdf(self, job_id: int) -> Optional[bytes]:
        """
        Retrieve the cover letter PDF for a specific job application.
        
        Args:
            job_id: The ID of the job application
            
        Returns:
            PDF binary data if exists, None otherwise
        """
        self.cursor.execute(
            "SELECT cover_letter_pdf FROM job_applications WHERE id = ?", 
            (job_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None

    def close(self):
        """Close the database connection."""
        # TODO: This should be at the end of the program
        self.conn.close()

if __name__ == "__main__":
    DATABASE_PATH = 'test.db'
    db = JobDatabase(DATABASE_PATH)

    db.close()