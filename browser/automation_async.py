import asyncio
import os
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page, ElementHandle


async def extract_fields(page: Page) -> List[Dict[str, Any]]:
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(500)

    elements = await page.query_selector_all("input,textarea,select")
    fields: List[Dict[str, Any]] = []

    for element in elements:
        try:
            tag_name = (await element.evaluate("el => el.tagName.toLowerCase()")) or ""
            input_type = (await element.get_attribute("type") or "").lower()
            if tag_name == "textarea":
                input_type = "textarea"
            if tag_name == "select":
                input_type = "select"
            if input_type == "hidden":
                continue

            if not await is_visible(element):
                continue

            name = (await element.get_attribute("name")) or (await element.get_attribute("id")) or ""
            placeholder = (await element.get_attribute("placeholder")) or ""
            label = await resolve_label(page, element, name)
            if not label:
                label = placeholder or name

            field = {
                "label": label.strip(),
                "type": input_type or tag_name,
                "name": name.strip(),
                "placeholder": placeholder.strip(),
                "element": element,
            }

            if field["type"] in ["checkbox", "radio", "file", "select", "textarea", "text", "email", "tel", "url", "number", "date", "search", "password"]:
                fields.append(field)
        except Exception:
            continue

    return fields


async def resolve_label(page: Page, element: ElementHandle, element_name: str) -> str:
    aria_label = await element.get_attribute("aria-label")
    if aria_label:
        return aria_label.strip()

    aria_labelledby = await element.get_attribute("aria-labelledby")
    if aria_labelledby:
        labels: List[str] = []
        for label_id in aria_labelledby.split():
            label_element = await page.query_selector(f"#{label_id}")
            if label_element:
                text = await label_element.text_content() or ""
                labels.append(text.strip())
        if labels:
            return " ".join(labels)

    if element_name:
        label_element = await page.query_selector(f'label[for="{element_name}"]')
        if label_element:
            text = await label_element.text_content() or ""
            if text.strip():
                return text.strip()

    closest_label = await element.evaluate(
        "el => { const label = el.closest('label'); return label ? label.innerText.trim() : ''; }"
    )
    if closest_label:
        return closest_label.strip()

    return ""


async def is_visible(element: ElementHandle) -> bool:
    try:
        if not await element.is_visible():
            return False
        if not await element.is_enabled():
            return False
        box = await element.bounding_box()
        if not box or box["width"] == 0 or box["height"] == 0:
            return False
        style = await element.evaluate(
            "el => ({ visibility: window.getComputedStyle(el).visibility, display: window.getComputedStyle(el).display, opacity: window.getComputedStyle(el).opacity })"
        )
        if style.get("visibility") == "hidden" or style.get("display") == "none" or style.get("opacity") == "0":
            return False
        return True
    except Exception:
        return False


def normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def map_field_to_profile(field: Dict[str, Any], profile: Dict[str, str], resume_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    label = normalize_text(field.get("label", ""))
    name = normalize_text(field.get("name", ""))
    placeholder = normalize_text(field.get("placeholder", ""))
    text = f"{label} {name} {placeholder}"

    if any(keyword in text for keyword in ["cookie", "consent", "privacy", "terms", "marketing", "tracking", "vendor", "optanon", "functional", "performance", "targeting"]):
        return None

    full_name = profile.get("name", "").strip()
    first_name = full_name.split()[0] if full_name else ""
    last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else ""

    if "first name" in text or "given name" in text:
        return {"action": "fill", "value": first_name}
    if "last name" in text or "surname" in text or "family name" in text:
        return {"action": "fill", "value": last_name}
    if "email" in text:
        return {"action": "fill", "value": profile.get("email", "")}
    if any(token in text for token in ["phone", "telephone", "mobile", "contact number", "cell"]):
        return {"action": "fill", "value": profile.get("phone", "")}
    if any(token in text for token in ["resume", "cv", "upload"]):
        if resume_path and os.path.exists(resume_path):
            return {"action": "file", "value": resume_path}
        return None
    if field["type"] == "checkbox" and any(token in text for token in ["agree", "accept", "yes", "consent"]):
        return {"action": "check", "value": True}
    if field["type"] == "radio" and any(token in text for token in ["yes", "no", "true", "false"]):
        return {"action": "check", "value": True}

    return None


async def fill_fields(page: Page, fields: List[Dict[str, Any]], profile: Dict[str, str], resume_path: Optional[str] = None) -> Dict[str, Any]:
    filled: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for field in fields:
        mapping = map_field_to_profile(field, profile, resume_path)
        if not mapping:
            skipped.append({"label": field["label"], "name": field["name"], "type": field["type"]})
            continue

        element = field["element"]
        try:
            await element.wait_for_element_state("visible", timeout=5000)
            await element.wait_for_element_state("enabled", timeout=5000)
        except Exception:
            pass

        action = mapping["action"]
        value = mapping.get("value")

        try:
            if action == "fill":
                if field["type"] in ["textarea", "text", "email", "tel", "url", "search", "number", "date", "password"]:
                    await element.fill(value or "")
                else:
                    await element.fill(value or "")
            elif action == "select":
                await select_option(element, value or "")
            elif action == "check":
                await element.check(force=True)
            elif action == "file":
                await element.set_input_files(value)
            else:
                skipped.append({"label": field["label"], "name": field["name"], "type": field["type"]})
                continue

            filled.append({"label": field["label"], "name": field["name"], "type": field["type"], "value": value})
        except Exception as exc:
            errors.append({"label": field["label"], "name": field["name"], "type": field["type"], "error": str(exc)})

    return {
        "total_detected": len(fields),
        "filled_count": len(filled),
        "skipped_count": len(skipped),
        "errors_count": len(errors),
        "filled": filled,
        "skipped": skipped,
        "errors": errors,
    }


async def select_option(element: ElementHandle, value: str) -> None:
    try:
        await element.select_option(value=value)
    except Exception:
        options = await element.query_selector_all("option")
        for option in options:
            text = (await option.text_content() or "").strip().lower()
            if value.lower() in text:
                option_value = await option.get_attribute("value")
                if option_value:
                    await element.select_option(value=option_value)
                    return
        if options:
            option_value = await options[0].get_attribute("value")
            if option_value:
                await element.select_option(value=option_value)


async def handle_cookie_popup(page: Page) -> None:
    button_texts = [
        "accept all", "accept cookies", "agree", "allow all", "continue", "ok", "yes", "accept"
    ]
    for text in button_texts:
        button = await page.query_selector(f"button:has-text(\"{text}\")")
        if button and await button.is_visible():
            try:
                await button.click(force=True)
                await page.wait_for_timeout(500)
            except Exception:
                continue


async def process_job_application(url: str, profile: Dict[str, str], resume_path: Optional[str] = None) -> Dict[str, Any]:
    async with async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=True)
        page: Page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        await handle_cookie_popup(page)
        fields = await extract_fields(page)
        summary = await fill_fields(page, fields, profile, resume_path)
        return summary


async def main() -> None:
    profile = {
        "name": "Ashish Rastogi",
        "email": "rastogiashish836@gmail.com",
        "phone": "8445631880",
    }
    resume_path = "./resume.pdf"
    url = "https://job-boards.greenhouse.io/greenhouse/jobs/7565603"
    summary = await process_job_application(url, profile, resume_path)
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
