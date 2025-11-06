// Simple test runner to convert a JSON string using convertIVSToExternal
// Usage: node scripts/test.js

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { convertIVSToExternal, hasIVSCharacters, countIVSCharacters } from '../src/utils/ivsUtils.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Provided JSON string (as-is). JS will decode \uXXXX escapes to actual code points.
const inputJsonText = `[
        {
            "year": "2025",
            "create_date": "2025-10-23",
            "base_date": "2025-10-23",
            "expire_date": null,
            "classes": [
                {
                    "school_name": "\u85e4\u679d\u660e\u8aa0\u9ad8\u7b49\u5b66\u6821",
                    "school_name_eng": "Fujieda Meisei High School",
                    "school_zipcd": "426-0051",
                    "school_pref_cd": "\u9759\u5ca1\u770c",
                    "school_addr1": "\u85e4\u679d\u5e02",
                    "school_addr2": "\u5927\u6d322\u4e01\u76ee2\u756a\u5730\u306e1",
                    "principal_name": "\u6e9d\u53e3\u3000\u4fe1\u5b50",
                    "grade_cd": "H1",
                    "grade_name": "\u7b2c1\u5b66\u5e74",
                    "grade_abbv": "\u9ad81",
                    "class_div": 1,
                    "class_cd": "H101",
                    "class_name": "1\u5e741\u7d44",
                    "hr_class_staffs": [
                        {
                            "class_cd": "H101",
                            "staff_div": 1,
                            "show_order": 1,
                            "staff_name": "\u5149\u5ca1\u3000\u5b5d"
                        }
                    ],
                    "enrollment": [
                        {
                            "enrollment_start_date": null,
                            "enrollment_end_date": null,
                            "attendance_no": "001",
                            "healthy_person_div": "\u5065\u5e38\u8005",
                            "major_cd": "0001",
                            "major_name": "\u666e\u901a\u79d1",
                            "major_name_eng": null,
                            "course_cd": "1101",
                            "course_name": "\u666e\u901a\u79d1",
                            "course_name_eng": "General Studies",
                            "student_id": null,
                            "school_register_no": "00025001",
                            "student_name": "\u3404\udb40\udd013404,E0101",
                            "student_name_kana": "\u3042\u3042\u3042\u3042",
                            "student_name_real": "\u66fe\udb40\udd02\u3404\udb40\udd01\u3404\udb40\udd00\u3404\u342c\u342c\udb40\udd02\u342e\u342e\udb40\udd02",
                            "student_name_real_kana": "\u3042\u3042\u3042\u3042",
                            "student_birthday": null,
                            "student_photo_face": null,
                            "student_sex": null,
                            "fin_school": "C123210001288",
                            "fin_date": "2025-03-31",
                            "fin_school_name": "\u8c4a\u6a4b\u5e02\u7acb\u9ad8\u5e2b\u53f0\u4e2d\u5b66\u6821",
                            "fin_school_abbv": "\u8c4a\u6a4b\u5e02\u7acb\u9ad8\u5e2b\u53f0\u4e2d\u5b66\u6821",
                            "fin_prischool": null,
                            "student_zip_cd": "000-0000",
                            "student_addr1": "XXXXXXX",
                            "student_addr2": "XXXXXXX",
                            "student_addr1_eng": "XXXXXXX",
                            "student_addr2_eng": "XXXXXXX",
                            "home_nearest_station": null,
                            "school_nearest_station": null,
                            "student_telno1": null,
                            "student_telno2": null,
                            "student_faxno": "000-0000",
                            "student_email": "XXXXX@example.com",
                            "emergency_contact_name1": "XXXXX",
                            "emergency_contact_telno1": null,
                            "emergency_contact_name2": "XXXXX",
                            "emergency_contact_telno2": null,
                            "matriculation_year": "2025",
                            "guardians": [
                                {
                                    "school_register_no": "00025001",
                                    "student_relation_div": "\u4fdd\u8b77\u8005\u7b49\u305d\u306e\uff11",
                                    "guardian_name": "11972",
                                    "guardian_name_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_name_real": "11972",
                                    "guardian_name_real_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_sex": null,
                                    "family_relationship": null,
                                    "guardian_zipno": "XXX-XXXX",
                                    "guardian_addr1": "XXXXXXX",
                                    "guardian_addr2": "XXXXXXX",
                                    "guardian_telno1": null,
                                    "guardian_telno2": null,
                                    "guardian_faxno": "XXX-XXXX",
                                    "guardian_email": "XXXXXXX@example.com",
                                    "occupation": "\uff0a\uff0a",
                                    "work_name": "\uff0a\uff0a\uff0a\uff0a",
                                    "work_telno": "XXX-XXXX",
                                    "living_together_flg": null,
                                    "remarks": null,
                                    "guardian_output_div": null
                                }
                            ],
                            "mat_clubs": [
                                {
                                    "school_register_no": "00025001",
                                    "club_cd": "",
                                    "club_name": "",
                                    "club_position": "",
                                    "club_start_date": "",
                                    "club_end_date": ""
                                }
                            ],
                            "mat_committees": []
                        },
                        {
                            "enrollment_start_date": null,
                            "enrollment_end_date": null,
                            "attendance_no": "002",
                            "healthy_person_div": "\u5065\u5e38\u8005",
                            "major_cd": "0001",
                            "major_name": "\u666e\u901a\u79d1",
                            "major_name_eng": null,
                            "course_cd": "1101",
                            "course_name": "\u666e\u901a\u79d1",
                            "course_name_eng": "General Studies",
                            "student_id": null,
                            "school_register_no": "00025002",
                            "student_name": "\u3404\udb40\udd003404,E0100",
                            "student_name_kana": "\u3042\u3042\u3042\u3042",
                            "student_name_real": "09790",
                            "student_name_real_kana": "\u3042\u3042\u3042\u3042",
                            "student_birthday": null,
                            "student_photo_face": null,
                            "student_sex": null,
                            "fin_school": "C122210000093",
                            "fin_date": "2025-03-31",
                            "fin_school_name": "\u6cbc\u6d25\u5e02\u7acb\u9759\u6d66\u4e2d\u5b66\u6821",
                            "fin_school_abbv": "\u6cbc\u6d25\u5e02\u7acb\u9759\u6d66\u4e2d\u5b66\u6821",
                            "fin_prischool": null,
                            "student_zip_cd": "0",
                            "student_addr1": "XXXXXXX",
                            "student_addr2": "XXXXXXX",
                            "student_addr1_eng": "XXXXXXX",
                            "student_addr2_eng": "XXXXXXX",
                            "home_nearest_station": null,
                            "school_nearest_station": null,
                            "student_telno1": null,
                            "student_telno2": null,
                            "student_faxno": "0",
                            "student_email": "XXXXX@example.com",
                            "emergency_contact_name1": "XXXXX",
                            "emergency_contact_telno1": null,
                            "emergency_contact_name2": "XXXXX",
                            "emergency_contact_telno2": null,
                            "matriculation_year": "2025",
                            "guardians": [
                                {
                                    "school_register_no": "00025002",
                                    "student_relation_div": "\u4fdd\u8b77\u8005\u7b49\u305d\u306e\uff11",
                                    "guardian_name": "11973",
                                    "guardian_name_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_name_real": "11973",
                                    "guardian_name_real_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_sex": null,
                                    "family_relationship": null,
                                    "guardian_zipno": "XXX-XXXX",
                                    "guardian_addr1": "XXXXXXX",
                                    "guardian_addr2": "XXXXXXX",
                                    "guardian_telno1": null,
                                    "guardian_telno2": null,
                                    "guardian_faxno": "XXX-XXXX",
                                    "guardian_email": "XXXXXXX@example.com",
                                    "occupation": "\uff0a\uff0a",
                                    "work_name": "\uff0a\uff0a\uff0a\uff0a",
                                    "work_telno": "XXX-XXXX",
                                    "living_together_flg": null,
                                    "remarks": null,
                                    "guardian_output_div": null
                                }
                            ],
                            "mat_clubs": [
                                {
                                    "school_register_no": "00025002",
                                    "club_cd": "",
                                    "club_name": "",
                                    "club_position": "",
                                    "club_start_date": "",
                                    "club_end_date": ""
                                }
                            ],
                            "mat_committees": []
                        },
                        {
                            "enrollment_start_date": null,
                            "enrollment_end_date": null,
                            "attendance_no": "003",
                            "healthy_person_div": "\u5065\u5e38\u8005",
                            "major_cd": "0001",
                            "major_name": "\u666e\u901a\u79d1",
                            "major_name_eng": null,
                            "course_cd": "1101",
                            "course_name": "\u666e\u901a\u79d1",
                            "course_name_eng": "General Studies",
                            "student_id": null,
                            "school_register_no": "00025003",
                            "student_name": "\u34043404,E0102",
                            "student_name_kana": "\u3042\u3042\u3042\u3042",
                            "student_name_real": "09791",
                            "student_name_real_kana": "\u3042\u3042\u3042\u3042",
                            "student_birthday": null,
                            "student_photo_face": null,
                            "student_sex": null,
                            "fin_school": "C122210001403",
                            "fin_date": "2025-03-31",
                            "fin_school_name": "\u713c\u6d25\u5e02\u7acb\u5927\u6751\u4e2d\u5b66\u6821",
                            "fin_school_abbv": "\u713c\u6d25\u5e02\u7acb\u5927\u6751\u4e2d\u5b66\u6821",
                            "fin_prischool": null,
                            "student_zip_cd": "0",
                            "student_addr1": "XXXXXXX",
                            "student_addr2": "XXXXXXX",
                            "student_addr1_eng": "XXXXXXX",
                            "student_addr2_eng": "XXXXXXX",
                            "home_nearest_station": null,
                            "school_nearest_station": null,
                            "student_telno1": null,
                            "student_telno2": null,
                            "student_faxno": "0",
                            "student_email": "XXXXX@example.com",
                            "emergency_contact_name1": "XXXXX",
                            "emergency_contact_telno1": null,
                            "emergency_contact_name2": "XXXXX",
                            "emergency_contact_telno2": null,
                            "matriculation_year": "2025",
                            "guardians": [
                                {
                                    "school_register_no": "00025003",
                                    "student_relation_div": "\u4fdd\u8b77\u8005\u7b49\u305d\u306e\uff11",
                                    "guardian_name": "11974",
                                    "guardian_name_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_name_real": "11974",
                                    "guardian_name_real_kana": "\u3042\u3042\u3042\u3042",
                                    "guardian_sex": null,
                                    "family_relationship": null,
                                    "guardian_zipno": "XXX-XXXX",
                                    "guardian_addr1": "XXXXXXX",
                                    "guardian_addr2": "XXXXXXX",
                                    "guardian_telno1": null,
                                    "guardian_telno2": null,
                                    "guardian_faxno": "XXX-XXXX",
                                    "guardian_email": "XXXXXXX@example.com",
                                    "occupation": "\uff0a\uff0a",
                                    "work_name": "\uff0a\uff0a\uff0a\uff0a",
                                    "work_telno": "XXX-XXXX",
                                    "living_together_flg": null,
                                    "remarks": null,
                                    "guardian_output_div": null
                                }
                            ],
                            "mat_clubs": [
                                {
                                    "school_register_no": "00025003",
                                    "club_cd": "",
                                    "club_name": "",
                                    "club_position": "",
                                    "club_start_date": "",
                                    "club_end_date": ""
                                }
                            ],
                            "mat_committees": []
                        }
                    ]
                }
            ]
        }
    ]`;

function main() {
  const hasBefore = hasIVSCharacters(inputJsonText);
  const countBefore = countIVSCharacters(inputJsonText);

  const convertedText = convertIVSToExternal(inputJsonText);

  const hasAfter = hasIVSCharacters(convertedText);
  const countAfter = countIVSCharacters(convertedText);

  // Ensure output directory exists
  const outDir = path.join(__dirname, '..', 'tmp');
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, 'converted.json');
  fs.writeFileSync(outFile, convertedText, 'utf8');

  console.log('IVS conversion test on JSON string');
  console.log(`  before: hasIVS=${hasBefore}, count=${countBefore}`);
  console.log(`  after : hasIVS=${hasAfter}, count=${countAfter}`);
  console.log(`  output: ${outFile}`);

  // Optional: try to parse JSON after conversion to validate (may still be valid)
  try {
    JSON.parse(convertedText);
    console.log('  parse : success (converted text is valid JSON)');
  } catch (e) {
    console.log('  parse : skipped (converted text may not be strict JSON due to PUA chars)');
  }
}

main();

