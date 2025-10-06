#!/usr/bin/env python
import os
import sys
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymlog_backend.settings')
django.setup()

from gym_app.models import Student

def clean_name(name):
    """
    Clean a name by:
    1. Removing middle initials (single letters followed by periods)
    2. Converting to proper case (first letter of each word capitalized)
    3. Removing extra spaces
    """
    if not name:
        return name
    
    # Remove middle initials (single letters followed by periods)
    # Pattern: word boundary + single letter + period + word boundary
    name = re.sub(r'\b[A-Z]\.\s*', '', name)
    
    # Remove extra spaces and trim
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Convert to proper case (first letter of each word capitalized, rest lowercase)
    name = name.title()
    
    return name

def check_current_names():
    """Check current student names to see what needs cleaning"""
    print("=== Current Student Names ===")
    
    # Get a sample of students to show current state
    students = Student.objects.all()[:10]  # First 10 students
    
    print(f"\nSample of current names (first 10 students):")
    for student in students:
        print(f"  {student.student_id}: {student.first_name} {student.last_name}")
    
    # Count students with potential middle initials
    total_students = Student.objects.count()
    print(f"\nTotal students in database: {total_students}")
    
    return students

def update_names():
    """Update all student names to clean format"""
    print("\n=== Updating Student Names ===")
    
    updated_count = 0
    students = Student.objects.all()
    
    for student in students:
        original_first = student.first_name
        original_last = student.last_name
        
        # Clean the names
        cleaned_first = clean_name(student.first_name)
        cleaned_last = clean_name(student.last_name)
        
        # Check if names actually changed
        if cleaned_first != original_first or cleaned_last != original_last:
            print(f"  {student.student_id}: '{original_first} {original_last}' → '{cleaned_first} {cleaned_last}'")
            
            # Update the student
            student.first_name = cleaned_first
            student.last_name = cleaned_last
            student.save()
            updated_count += 1
    
    print(f"\nUpdated {updated_count} student names")
    return updated_count

def verify_updates():
    """Verify that the name updates were successful"""
    print("\n=== Verification ===")
    
    # Show some examples of cleaned names
    students = Student.objects.all()[:10]
    
    print(f"\nSample of cleaned names (first 10 students):")
    for student in students:
        print(f"  {student.student_id}: {student.first_name} {student.last_name}")
    
    # Check for any remaining middle initials
    students_with_initials = []
    for student in Student.objects.all():
        if re.search(r'\b[A-Z]\.', student.first_name) or re.search(r'\b[A-Z]\.', student.last_name):
            students_with_initials.append(student)
    
    if students_with_initials:
        print(f"\n⚠️  Found {len(students_with_initials)} students with remaining middle initials:")
        for student in students_with_initials[:5]:  # Show first 5
            print(f"  {student.student_id}: {student.first_name} {student.last_name}")
        if len(students_with_initials) > 5:
            print(f"  ... and {len(students_with_initials) - 5} more")
    else:
        print("✅ All middle initials successfully removed!")

if __name__ == "__main__":
    print("Starting student name cleanup process...")
    
    # Check current state
    check_current_names()
    
    # Perform updates
    update_names()
    
    # Verify updates
    verify_updates()
    
    print("\nStudent name cleanup process completed!")
