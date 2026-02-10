import sqlite3
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
                source TEXT,
                job_type TEXT,
                date_applied TEXT,
                contact_name TEXT,
                contact_email TEXT,
                salary_range TEXT,
                work_arrangement TEXT,
                office_days INTEGER NULL,
                job_url TEXT,
                job_description TEXT,
                notes TEXT,
                cv_pdf BLOB,
                cv_text TEXT,
                cover_letter_pdf BLOB,
                cover_letter_text TEXT,
                last_update TEXT
                )""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cv_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                newest_version_id INTEGER,
                FOREIGN KEY (newest_version_id)
                    REFERENCES cv_version(id)
                    ON DELETE SET NULL
                )""")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cv_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cv_group_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                json_path TEXT NOT NULL,
                pdf_path TEXT,
                FOREIGN KEY (cv_group_id)
                    REFERENCES cv_group(id)
                    ON DELETE CASCADE
                )""")
    
        self.conn.commit()
    
    def add_job(self, 
            company: str, 
            position: str, 
            status: str,
            company_website: Optional[str] = None,
            location: Optional[str] = None,
            source: Optional[str] = None,
            job_type: Optional[str] = None,
            date_applied: Optional[str] = None,
            contact_name: Optional[str] = None,
            contact_email: Optional[str] = None,
            salary_range: Optional[str] = None,
            work_arrangement: Optional[str] = None,
            office_days: Optional[int] = None,
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
                work_arrangement, office_days,
                job_url, job_description, notes, cv_pdf, cv_text,
                cover_letter_pdf, cover_letter_text, last_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company, company_website, position, status, location,
            date_applied, contact_name, contact_email, salary_range,
            work_arrangement, office_days,
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
            source: Optional[str] = None,
            job_type: Optional[str] = None,
            date_applied: Optional[str] = None,
            contact_name: Optional[str] = None,
            contact_email: Optional[str] = None,
            salary_range: Optional[str] = None,
            work_arrangement: Optional[str] = None,
            office_days: Optional[int] = None,
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
        if source is not None:
            fields_to_update.append("source = ?")
            values.append(source)
        if job_type is not None:
            fields_to_update.append("job_type = ?")
            values.append(job_type)
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
        if work_arrangement is not None:
            fields_to_update.append("work_arrangement = ?")
            values.append(work_arrangement)
        if work_arrangement is not None or office_days is not None:
            fields_to_update.append("office_days = ?")
            values.append(office_days)
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
                   source, job_type, 
                   date_applied, contact_name, contact_email, salary_range,
                   work_arrangement, office_days,
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

    def get_all_cv_groups(self) -> List[Tuple]:
        """
        Retrieve all CV groups ordered by last update.

        Returns:
            List of tuples: (id, title, created_at, updated_at, newest_version_id)
        """
        self.cursor.execute("""
            SELECT id, title, created_at, updated_at, newest_version_id
            FROM cv_group
            ORDER BY updated_at DESC
        """)
        return self.cursor.fetchall()

    def get_newest_cv_json_path(self, cv_group_id: int) -> Optional[str]:
        """
        Retrieve the JSON path of the newest CV version for a given CV group.

        Args:
            cv_group_id: ID of the CV group

        Returns:
            JSON path as string, or None if not found
        """
        self.cursor.execute("""
            SELECT v.json_path
            FROM cv_group g
            JOIN cv_version v ON v.id = g.newest_version_id
            WHERE g.id = ?
        """, (cv_group_id,))

        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_cv_versions(self, cv_group_id: int) -> List[Tuple]:
        """
        Retrieve all CV versions for a given CV group.

        Args:
            cv_group_id: ID of the CV group

        Returns:
            List of tuples: (json_path, created_at)
        """
        self.cursor.execute("""
            SELECT json_path, created_at
            FROM cv_version
            WHERE cv_group_id = ?
            ORDER BY created_at DESC
        """, (cv_group_id,))

        return self.cursor.fetchall()

    def create_cv_group(self, title: str, created_at: str) -> int:
        """
        Create a new CV group.

        Args:
            title: Display title of the CV group
            created_at: Creation timestamp (ISO string)

        Returns:
            ID of the newly created CV group
        """
        self.cursor.execute("""
            INSERT INTO cv_group (title, created_at, updated_at, newest_version_id)
            VALUES (?, ?, ?, NULL)
        """, (title, created_at, created_at))

        self.conn.commit()
        return self.cursor.lastrowid

    def create_cv_version(
        self,
        cv_group_id: int,
        created_at: str,
        json_path: str,
        pdf_path: str | None = None,
        docx_path: str | None = None,
        checksum: str | None = None
        ) -> int:
        """
        Create a new immutable CV version and mark it as newest for the group.

        Args:
            cv_group_id: ID of the CV group
            created_at: Creation timestamp (ISO string)
            json_path: Path to the JSON snapshot
            pdf_path: Optional PDF path
            docx_path: Optional DOCX path
            checksum: Optional checksum of the JSON file

        Returns:
            ID of the newly created CV version
        """
        try:
            self.cursor.execute("BEGIN")

            self.cursor.execute("""
                INSERT INTO cv_version (
                    cv_group_id,
                    created_at,
                    json_path,
                    pdf_path,
                    docx_path,
                    checksum
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cv_group_id,
                created_at,
                json_path,
                pdf_path,
                docx_path,
                checksum
            ))

            version_id = self.cursor.lastrowid

            self.cursor.execute("""
                UPDATE cv_group
                SET newest_version_id = ?,
                    updated_at = ?
                WHERE id = ?
            """, (version_id, created_at, cv_group_id))

            self.conn.commit()
            return version_id

        except Exception:
            self.conn.rollback()
            raise

    def delete_cv_group(self, cv_group_id: int) -> None:
        """
        Delete a CV group and all associated CV versions.

        Args:
            cv_group_id: ID of the CV group to delete
        """
        self.cursor.execute("""
            DELETE FROM cv_group
            WHERE id = ?
        """, (cv_group_id,))

        self.conn.commit()


    def close(self):
        """Close the database connection."""
        # TODO: This should be at the end of the program
        self.conn.close()

if __name__ == "__main__":
    DATABASE_PATH = 'test.db'
    db = JobDatabase(DATABASE_PATH)

    db.close()