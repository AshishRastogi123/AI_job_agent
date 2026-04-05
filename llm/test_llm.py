#!/usr/bin/env python3
"""
Test script for LLM components
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.resume_generator import generate_resume
from llm.cover_letter import generate_cover_letter
from llm.field_inference import infer_field

def test_resume_generation():
    """Test resume generation"""
    print("Testing Resume Generation...")

    profile = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "work_experience": [
            {
                "company": "Tech Corp",
                "position": "Software Engineer",
                "start_date": "2021-06-01",
                "end_date": "2024-01-01",
                "description": "Developed web applications using Python and React. Led a team of 3 developers."
            }
        ],
        "education": [
            {
                "institution": "State University",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "2015-09-01",
                "end_date": "2019-05-31",
                "gpa": 3.8
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "Expert"},
            {"name": "JavaScript", "proficiency": "Advanced"}
        ]
    }

    job_description = """
    Senior Python Developer position at Innovative Tech Solutions.

    Requirements:
    - 3+ years Python development experience
    - Experience with web frameworks (Django/Flask)
    - Knowledge of REST APIs and database design
    - Familiarity with cloud platforms (AWS/Azure)

    Responsibilities:
    - Develop and maintain Python-based web applications
    - Design and implement RESTful APIs
    - Collaborate with cross-functional teams
    - Deploy applications to cloud infrastructure
    """

    try:
        resume = generate_resume(profile, job_description)
        print("✅ Resume generated successfully")
        print(f"Length: {len(resume)} characters")
        print("Sample output:")
        print(resume[:500] + "..." if len(resume) > 500 else resume)
        return True
    except Exception as e:
        print(f"❌ Resume generation failed: {e}")
        return False

def test_cover_letter_generation():
    """Test cover letter generation"""
    print("\nTesting Cover Letter Generation...")

    profile = {
        "name": "John Doe",
        "work_experience": [
            {
                "company": "Tech Corp",
                "position": "Software Engineer"
            }
        ]
    }

    job_description = "Senior Python Developer position requiring 3+ years experience with Django and AWS."

    try:
        cover_letter = generate_cover_letter(profile, job_description)
        print("✅ Cover letter generated successfully")
        print(f"Length: {len(cover_letter)} characters")
        print("Sample output:")
        print(cover_letter[:300] + "..." if len(cover_letter) > 300 else cover_letter)
        return True
    except Exception as e:
        print(f"❌ Cover letter generation failed: {e}")
        return False

def test_field_inference():
    """Test field inference"""
    print("\nTesting Field Inference...")

    profile = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": ["Python", "JavaScript"]
    }

    field_name = "Why are you interested in this position?"

    try:
        response = infer_field(field_name, profile)
        print("✅ Field inference successful")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Field inference failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running LLM Component Tests\n")

    results = []
    results.append(test_resume_generation())
    results.append(test_cover_letter_generation())
    results.append(test_field_inference())

    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check your API keys and configuration.")

if __name__ == "__main__":
    main()