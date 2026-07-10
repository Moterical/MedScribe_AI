from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.utils import create_clinical_brief_pdf
from datetime import datetime

import json

# 1. log_interaction Schema
class SampleItem(BaseModel):
    sample_name: str
    quantity: int

class LogInteractionInput(BaseModel):
    hcp_name: Optional[str] = Field(default=None, description="The name of the Healthcare Professional (HCP), e.g. Dr. Smith")
    interaction_type: Optional[str] = Field(default=None, description="Type of meeting: 'Meeting', 'Email', 'Call', 'Other'")
    date: Optional[str] = Field(default=None, description="Date of interaction.")
    time: Optional[str] = Field(default=None, description="Time of interaction.")
    attendees: Optional[str] = Field(default=None, description="Other attendees besides the HCP and rep (comma-separated).")
    topics_discussed: Optional[str] = Field(default=None, description="Summary of key discussion topics.")
    sentiment: Optional[str] = Field(default=None, description="Observed sentiment of the HCP: 'Positive', 'Neutral', 'Negative'.")
    outcomes: Optional[str] = Field(default=None, description="Outcomes or agreements of the meeting.")
    follow_up_actions: Optional[str] = Field(default=None, description="Any immediate follow-up tasks.")
    samples: Optional[Any] = Field(default=None, description="Details of drug/product samples distributed, with quantity. Can be a list of objects with 'sample_name' and 'quantity', a JSON string, or a plain text description. Only include samples that were actually handed out/distributed. If the product name is not explicitly mentioned, infer it based on the topics discussed.")
    materials: Optional[Any] = Field(default=None, description="List of materials/brochures shared. Can be a list, comma-separated string, or JSON string.")

# 2. edit_interaction Schema
class EditInteractionInput(BaseModel):
    field_name: str = Field(description="The specific field name to modify: 'hcp_name', 'interaction_type', 'date', 'time', 'attendees', 'topics_discussed', 'sentiment', 'outcomes', 'follow_up_actions'")
    new_value: str = Field(description="The new value to write to the field.")

# 3. generate_study_pdf Schema
class GenerateStudyPdfInput(BaseModel):
    hcp_name: str = Field(description="Name of the HCP.")
    topics_discussed: str = Field(description="The topics discussed that should anchor the clinical trial summary.")
    custom_clinical_summary: str = Field(description="A 2-3 paragraph custom clinical brief detailing efficacy, trials, and safety profile regarding the topics discussed.")

# 4. generate_followup_email Schema
class GenerateFollowupEmailInput(BaseModel):
    hcp_name: str = Field(description="Name of the HCP.")
    topics_discussed: str = Field(description="Topics discussed.")
    outcomes: Optional[str] = Field(default="", description="Outcomes of the interaction.")
    recipient_email: Optional[str] = Field(default=None, description="Optional email address to send the draft to. If provided, simulates sending.")

# 5. schedule_calendar_event Schema
class ScheduleCalendarEventInput(BaseModel):
    meeting_date: str = Field(description="Date for the follow-up meeting.")
    meeting_time: str = Field(description="Time for the follow-up meeting.")
    attendees: Optional[str] = Field(default=None, description="Attendees list.")
    subject: Optional[str] = Field(default="Follow-up HCP Discussion", description="Subject of the meeting.")

class SchedulingCalendarEventInput(ScheduleCalendarEventInput):
    pass



def normalize_time(time_str: str) -> str:
    if not time_str:
        return ""
    t = time_str.strip().lower()
    
    # Strip dots from "p.m." or "a.m."
    t = t.replace(".", "")
    
    is_pm = "pm" in t
    is_am = "am" in t
    
    # Clean non-digit characters besides colon
    t_digits = ""
    for char in t:
        if char.isdigit() or char == ":":
            t_digits += char
            
    # Now parse hours and minutes
    parts = t_digits.split(":")
    if len(parts) == 2:
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError:
            return "12:00"
    elif len(parts) == 1:
        try:
            hour = int(parts[0])
            minute = 0
        except ValueError:
            return "12:00"
    else:
        return "12:00"
        
    # Adjust for AM/PM
    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
        
    return f"{hour:02d}:{minute:02d}"


def normalize_date(date_str: str) -> str:
    if not date_str:
        return ""
    d = date_str.strip().lower()
    
    # Handle relative dates
    from datetime import timedelta
    today = datetime.now()
    if "today" in d:
        return today.strftime("%Y-%m-%d")
    elif "tomorrow" in d:
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    elif "next week" in d:
        next_week = today + timedelta(days=7)
        return next_week.strftime("%Y-%m-%d")
        
    # Clean ordinal suffixes only when they follow a number (e.g. "14th", "1st", "22nd") so we don't corrupt month names like "August"
    import re
    d_clean = re.sub(r'(\d+)(?:st|nd|rd|th)\b', r'\1', d, flags=re.IGNORECASE)
    d_clean = d_clean.replace(",", "").strip()
    
    # Try parsing patterns
    for fmt in ("%y-%m-%d", "%y/%m/%d", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%dt%h:%m:%s"):
      try:
        parsed = datetime.strptime(d_clean, fmt)
        return parsed.strftime("%Y-%m-%d")
      except ValueError:
        continue
            
    # Try parsing text-based formats e.g. "august 20 2026"
    for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
      try:
        parsed = datetime.strptime(d_clean.title(), fmt)
        return parsed.strftime("%Y-%m-%d")
      except ValueError:
        continue
            
    # If parsing failed, append current year and try again
    current_year = str(today.year)
    d_with_year = f"{d_clean} {current_year}"
    for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
      try:
        parsed = datetime.strptime(d_with_year.title(), fmt)
        return parsed.strftime("%Y-%m-%d")
      except ValueError:
        continue
            
    # Try parsing numerical formats like "08-20" or "08/20" by appending year
    for sep in ("-", "/"):
      parts = d_clean.split(sep)
      if len(parts) == 2:
        try:
          test_str = f"{parts[0]}{sep}{parts[1]}{sep}{current_year}"
          parsed = datetime.strptime(test_str, f"%m{sep}%d{sep}%Y")
          return parsed.strftime("%Y-%m-%d")
        except ValueError:
          try:
            test_str = f"{parts[0]}{sep}{parts[1]}{sep}{current_year}"
            parsed = datetime.strptime(test_str, f"%d{sep}%m{sep}%Y")
            return parsed.strftime("%Y-%m-%d")
          except ValueError:
            continue

    # Fallback: if it's already a valid YYYY-MM-DD string, return it, otherwise return None to prevent schema crashes
    try:
      datetime.strptime(date_str.strip(), "%Y-%m-%d")
      return date_str.strip()
    except ValueError:
      return None


def execute_tool_action(name: str, args: Dict[str, Any], current_form: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """
    Executes a tool on the current form state.
    Returns (updated_form_dict, tool_result_string).
    """
    updated_form = current_form.copy()
    
    # Initialize list properties if not present
    if "samples" not in updated_form:
        updated_form["samples"] = []
    if "materials" not in updated_form:
        updated_form["materials"] = []

    if name == "log_interaction":
        # Overwrite/fill out fields only if they are explicitly passed in arguments (not None)
        if args.get("hcp_name") is not None:
            updated_form["hcp_name"] = args["hcp_name"]
        if args.get("interaction_type") is not None:
            updated_form["interaction_type"] = args["interaction_type"]
        if args.get("date"):
            norm_d = normalize_date(args["date"])
            if norm_d:
                updated_form["interaction_date"] = norm_d
        if args.get("time"):
            norm_t = normalize_time(args["time"])
            if norm_t:
                updated_form["interaction_time"] = norm_t
        if args.get("attendees") is not None:
            updated_form["attendees"] = args["attendees"]
        if args.get("topics_discussed") is not None:
            updated_form["topics_discussed"] = args["topics_discussed"]
        if args.get("sentiment") is not None:
            updated_form["sentiment"] = args["sentiment"]
        if args.get("outcomes") is not None:
            updated_form["outcomes"] = args["outcomes"]
        if args.get("follow_up_actions") is not None:
            updated_form["follow_up_actions"] = args["follow_up_actions"]
        
        # Parse samples defensively
        if args.get("samples") is not None:
            samples_raw = args.get("samples")
            samples_list = []
            
            # Pre-parse string containing dictionary representation
            if isinstance(samples_raw, str):
                cleaned = samples_raw.strip()
                if cleaned.startswith("{") and cleaned.endswith("}"):
                    try:
                        import ast
                        dict_val = ast.literal_eval(cleaned)
                        if isinstance(dict_val, dict):
                            samples_raw = dict_val
                    except Exception:
                        pass

            # If it is a dictionary, wrap in a list or parse key-value map
            if isinstance(samples_raw, dict):
                # Check if it has a key that contains the list of samples
                has_list_key = False
                for key in ["samples", "data", "list", "items", "distributed_samples", "distributed"]:
                    if key in samples_raw and isinstance(samples_raw[key], list):
                        samples_list = samples_raw[key]
                        has_list_key = True
                        break
                
                if not has_list_key:
                    # Check if it is a key-value map of {product_name: quantity}
                    # e.g., {"Hypertension Tablets": 5}
                    samples_list = []
                    for k, v in samples_raw.items():
                        try:
                            # If value is an integer or can be converted to one
                            val_int = int(v)
                            # Make sure the key isn't a schema keyword
                            if k.lower() not in ["total", "remaining", "in_bag", "inventory", "total_samples", "in_bag_samples"]:
                                samples_list.append({"sample_name": str(k), "quantity": val_int})
                        except (ValueError, TypeError):
                            continue
            # If it is a list, use it
            elif isinstance(samples_raw, list):
                samples_list = samples_raw
            # If it is a string
            elif isinstance(samples_raw, str):
                cleaned = samples_raw.strip()
                # Check if it's a JSON list
                if cleaned.startswith("[") and cleaned.endswith("]"):
                    try:
                        samples_list = json.loads(cleaned)
                    except Exception:
                        pass
                elif cleaned:
                    # Try to parse strings like "2 samples", "2 units of OncoBoost", "5 vials"
                    import re
                    match = re.search(r'(\d+)\s*(?:samples?|units?|items?|vials?|packages?|tablets?)?\s*(?:of\s+)?(.*)', cleaned, re.IGNORECASE)
                    if match:
                        qty = int(match.group(1))
                        name = match.group(2).strip()
                        if not name:
                            name = f"{args.get('topics_discussed') or 'Product'} Sample"
                        samples_list = [{"sample_name": name, "quantity": qty}]
                    else:
                        if cleaned.isdigit():
                            name = f"{args.get('topics_discussed') or 'Product'} Sample"
                            samples_list = [{"sample_name": name, "quantity": int(cleaned)}]
                        else:
                            samples_list = [{"sample_name": cleaned, "quantity": 1}]
            # If it is a number (int or float)
            elif isinstance(samples_raw, (int, float)):
                name = f"{args.get('topics_discussed') or 'Product'} Sample"
                samples_list = [{"sample_name": name, "quantity": int(samples_raw)}]
                
            final_samples = []
            for s in samples_list:
                name = None
                qty = 1
                if isinstance(s, dict):
                    name = s.get("sample_name") or s.get("name")
                    qty = s.get("quantity") or s.get("qty")
                elif isinstance(s, str):
                    name = s
                    qty = 1
                elif hasattr(s, "dict"):
                    s_dict = s.dict()
                    name = s_dict.get("sample_name")
                    qty = s_dict.get("quantity")

                # Parse and clean name
                if name:
                    import re
                    # Strip out action details like "given to the doctor out of 5 in the bag", "remaining", etc.
                    name = re.sub(r'\s*(?:given|handed|distributed|delivered|shared|sent)\s*(?:to\s*(?:the\s*)?(?:doctor|hcp))?.*', '', name, flags=re.IGNORECASE)
                    name = re.sub(r'\s*out\s+of\s+\d+.*', '', name, flags=re.IGNORECASE)
                    name = re.sub(r'\s*in\s+the\s+bag.*', '', name, flags=re.IGNORECASE)
                    name = name.strip()

                if not name:
                    name = f"{args.get('topics_discussed') or 'Product'} Sample"

                try:
                    qty = int(qty) if qty is not None else 1
                except ValueError:
                    qty = 1

                final_samples.append({
                    "sample_name": name,
                    "quantity": qty
                })
            updated_form["samples"] = final_samples
        
        # Parse materials defensively
        if args.get("materials") is not None:
            mats_raw = args.get("materials")
            mats = []
            
            # Pre-parse string containing dictionary representation
            if isinstance(mats_raw, str):
                cleaned = mats_raw.strip()
                if cleaned.startswith("{") and cleaned.endswith("}"):
                    try:
                        import ast
                        dict_val = ast.literal_eval(cleaned)
                        if isinstance(dict_val, dict):
                            mats_raw = dict_val
                    except Exception:
                        pass

            if isinstance(mats_raw, str):
                cleaned = mats_raw.strip()
                if cleaned.startswith("[") and cleaned.endswith("]"):
                    try:
                        mats = json.loads(cleaned)
                    except Exception:
                        mats = [x.strip().strip('"\'') for x in cleaned[1:-1].split(",") if x.strip()]
                else:
                    mats = [x.strip() for x in mats_raw.split(",") if x.strip()]
            elif isinstance(mats_raw, list):
                mats = mats_raw
            elif isinstance(mats_raw, dict):
                mats = []
                for k, v in mats_raw.items():
                    try:
                        val_int = int(v)
                        if val_int > 1:
                            mats.append(f"{k} (x{val_int})")
                        else:
                            mats.append(str(k))
                    except (ValueError, TypeError):
                        mats.append(str(k))
            else:
                mats = []

            for m in mats:
                if m and m not in updated_form["materials"]:
                    updated_form["materials"].append(m)

        return updated_form, f"Logged interaction details for {updated_form.get('hcp_name', 'HCP')} successfully."

    elif name == "edit_interaction":
        field = args.get("field_name")
        val = args.get("new_value")
        
        # Map fields to actual keys in DB state
        field_mapping = {
            "hcp_name": "hcp_name",
            "interaction_type": "interaction_type",
            "date": "interaction_date",
            "time": "interaction_time",
            "attendees": "attendees",
            "topics_discussed": "topics_discussed",
            "sentiment": "sentiment",
            "outcomes": "outcomes",
            "follow_up_actions": "follow_up_actions"
        }
        
        target_field = field_mapping.get(field)
        if target_field:
            if target_field == "interaction_date":
                val = normalize_date(val)
            elif target_field == "interaction_time":
                val = normalize_time(val)
            updated_form[target_field] = val
            return updated_form, f"Field '{field}' successfully updated to: {val}"
        else:
            return updated_form, f"Error: Field '{field}' is not editable."

    elif name == "generate_study_pdf":
        hcp = args.get("hcp_name") or updated_form.get("hcp_name") or "Healthcare Professional"
        topics = args.get("topics_discussed") or updated_form.get("topics_discussed") or "Product Efficacy"
        summary = args.get("custom_clinical_summary")
        
        # Trigger ReportLab generation
        pdf_filename = create_clinical_brief_pdf(
            hcp_name=hcp,
            topics=topics,
            content=summary,
            samples=updated_form.get("samples", []),
            materials=updated_form.get("materials", [])
        )
        
        # Update path in form
        updated_form["pdf_path"] = f"/api/interactions/download-pdf/{pdf_filename}"
        
        # Append to materials list if not already present
        brief_label = f"Clinical Brief - {topics[:30]}"
        if brief_label not in updated_form["materials"]:
            updated_form["materials"].append(brief_label)

        return updated_form, f"Successfully generated dynamic Clinical Trial Briefing PDF: {pdf_filename}. Attached to Materials Shared."

    elif name == "generate_followup_email":
        hcp = args.get("hcp_name") or updated_form.get("hcp_name") or "Doctor"
        topics = args.get("topics_discussed") or updated_form.get("topics_discussed") or "Product Detail"
        outcomes = args.get("outcomes") or updated_form.get("outcomes") or "Follow-up items"
        email = args.get("recipient_email")
        
        email_body = (
            f"Subject: Follow-up regarding our discussion on {topics}\n\n"
            f"Dear {hcp},\n\n"
            f"Thank you for taking the time to speak with me today. It was great discussing {topics} with you.\n\n"
            f"As discussed, we have noted the following outcomes/agreements: {outcomes}.\n"
            f"If you have any further questions or require additional clinical data, please feel free to reach out.\n\n"
            f"Best regards,\n"
            f"Medical Representative"
        )
        
        updated_form["email_draft"] = email_body
        
        if email:
            updated_form["email_sent_to"] = email
            return updated_form, f"Follow-up email draft generated and simulated sent to {email}:\n\n{email_body}"
        else:
            return updated_form, f"Follow-up email draft generated (saved to form state):\n\n{email_body}"

    elif name == "schedule_calendar_event":
        m_date = normalize_date(args.get("meeting_date"))
        m_time = normalize_time(args.get("meeting_time"))
        subj = args.get("subject", "Follow-up meeting")
        
        # Set follow up task text in form
        sched_text = f"Follow-up scheduled: {subj} on {m_date} at {m_time}"
        updated_form["follow_up_actions"] = sched_text
        updated_form["open_calendar_picker"] = True
        updated_form["calendar_event"] = {
            "date": m_date,
            "time": m_time,
            "subject": subj
        }
        
        return updated_form, f"Successfully scheduled '{subj}' for {m_date} at {m_time}. UI calendar scheduler has been activated."

    return updated_form, "Unknown tool execution requested."
