const form = document.getElementById("resume-form");

if (form) {
    const initialDataElement = document.getElementById("initial-resume-data");
    const initialData = initialDataElement ? JSON.parse(initialDataElement.textContent || "{}") : {};

    const templateInput = document.getElementById("template");
    const profileImageDataInput = document.getElementById("profile_image_data");
    const profileImageFileInput = document.getElementById("profile_image_file");
    const formImagePreview = document.getElementById("form-image-preview");
    const previewFrame = document.getElementById("preview-box");
    const resumeSheet = document.getElementById("resume-sheet");

    const previewHeader = document.getElementById("preview-header");
    const previewName = document.getElementById("preview-name");
    const previewRole = document.getElementById("preview-role");
    const previewMeta = document.getElementById("preview-meta");
    const previewContactSection = document.getElementById("preview-contact-section");
    const previewContactList = document.getElementById("preview-contact-list");
    const previewProfileImageWrap = document.getElementById("preview-profile-image-wrap");
    const previewProfileImage = document.getElementById("preview-profile-image");

    const previewSummarySection = document.getElementById("preview-summary-section");
    const previewSummaryTitle = document.getElementById("preview-summary-title");
    const previewSummary = document.getElementById("preview-summary");

    const previewEducationSection = document.getElementById("preview-education-section");
    const previewEducationList = document.getElementById("preview-education-list");

    const previewSkillsSection = document.getElementById("preview-skills-section");
    const previewSkillsList = document.getElementById("preview-skills-list");

    const previewProjectsSection = document.getElementById("preview-projects-section");
    const previewProjectsList = document.getElementById("preview-projects-list");

    const previewWorkSection = document.getElementById("preview-work-experience-section");
    const previewWorkList = document.getElementById("preview-work-experience-list");

    const previewCertificationsSection = document.getElementById("preview-certifications-section");
    const previewCertificationsList = document.getElementById("preview-certifications-list");

    const previewAchievementsSection = document.getElementById("preview-achievements-section");
    const previewAchievementsList = document.getElementById("preview-achievements-list");
    const previewCustomSections = document.getElementById("preview-custom-sections");
    const resumeScoreBtn = document.getElementById("resumeScoreBtn");
    const atsScoreModal = document.getElementById("atsScoreModal");
    const atsScoreStatus = document.getElementById("atsScoreStatus");
    const atsScoreValue = document.getElementById("atsScoreValue");
    const atsRoleMatch = document.getElementById("atsRoleMatch");
    const atsBreakdownList = document.getElementById("atsBreakdownList");
    const atsMissingSkillsList = document.getElementById("atsMissingSkillsList");
    const atsSuggestionsList = document.getElementById("atsSuggestionsList");
    const atsAnalysisNotesList = document.getElementById("atsAnalysisNotesList");

    const templateCards = [...document.querySelectorAll("[data-template-card]")];

    const sectionConfig = {
        education: {
            containerId: "education-list",
            templateId: "education-entry-template",
            hiddenInputId: "education_json",
            fields: ["institution", "degree", "specialization", "start_year", "end_year", "score"],
        },
        projects: {
            containerId: "projects-list",
            templateId: "projects-entry-template",
            hiddenInputId: "projects_json",
            fields: ["title", "url", "description", "technologies"],
        },
        work_experience: {
            containerId: "work-experience-list",
            templateId: "work-experience-entry-template",
            hiddenInputId: "work_experience_json",
            fields: ["company", "role", "start_date", "end_date", "description"],
        },
        certifications: {
            containerId: "certifications-list",
            templateId: "certifications-entry-template",
            hiddenInputId: "certifications_json",
            fields: ["title", "issuer", "url", "year"],
        },
        achievements: {
            containerId: "achievements-list",
            templateId: "achievements-entry-template",
            hiddenInputId: "achievements_json",
            fields: ["text"],
        },
        custom_sections: {
            containerId: "custom-sections-list",
            templateId: "custom-sections-entry-template",
            hiddenInputId: "custom_sections_json",
            fields: ["title", "content"],
        },
    };

    const skillFieldIds = [
        "languages",
        "web_technologies",
        "frameworks",
        "databases",
        "tools_platforms",
        "core_concepts",
        "testing",
        "cloud_devops",
    ];

    const skillFieldLabels = {
        languages: "Languages",
        web_technologies: "Web Technologies",
        frameworks: "Frameworks",
        databases: "Databases",
        tools_platforms: "Tools & Platforms",
        core_concepts: "Core Concepts",
        testing: "Testing",
        cloud_devops: "Cloud & DevOps",
    };

    function trimValue(value) {
        return typeof value === "string" ? value.trim() : "";
    }

    function splitSkillItems(value) {
        return trimValue(value)
            .split(/[\n,]+/)
            .map((item) => item.trim())
            .filter(Boolean);
    }

    function createTextElement(tag, className, text) {
        const element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        element.textContent = text;
        return element;
    }

    function createIconElement(iconId) {
        const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        icon.setAttribute("class", "contact-icon");
        icon.setAttribute("aria-hidden", "true");

        const useElement = document.createElementNS("http://www.w3.org/2000/svg", "use");
        useElement.setAttribute("href", `#icon-${iconId}`);
        icon.appendChild(useElement);

        return icon;
    }

    function buildLinkValue(value, type) {
        const trimmed = trimValue(value);
        if (!trimmed) {
            return "";
        }

        if (type === "email") {
            return `mailto:${trimmed}`;
        }

        if (type === "phone") {
            const digits = trimmed.replace(/[^\d+]/g, "");
            return digits ? `tel:${digits}` : "";
        }

        if (/^(https?:\/\/|mailto:|tel:)/i.test(trimmed)) {
            return trimmed;
        }

        return `https://${trimmed}`;
    }

    function createContactItem(type, value) {
        const item = document.createElement("a");
        item.className = "resume-meta__item";
        item.href = buildLinkValue(value, type);
        item.target = "_blank";
        item.rel = "noreferrer";
        item.appendChild(createIconElement(type));
        item.appendChild(createTextElement("span", "", value));
        return item;
    }

    function createSidebarContactItem(type, value) {
        const item = document.createElement("a");
        item.className = "contact-list__item";
        item.href = buildLinkValue(value, type);
        item.target = "_blank";
        item.rel = "noreferrer";
        item.appendChild(createIconElement(type));
        item.appendChild(createTextElement("span", "", value));
        return item;
    }

    function buildDateText(startValue, endValue) {
        const startDate = trimValue(startValue);
        const endDate = trimValue(endValue);

        if (startDate && endDate) {
            return `${startDate} - ${endDate}`;
        }

        return startDate || endDate;
    }

    function buildEducationTitle(entry) {
        const degree = trimValue(entry.degree);
        const specialization = trimValue(entry.specialization);

        if (degree && specialization) {
            return `${degree} in ${specialization}`;
        }

        return degree || specialization || trimValue(entry.institution);
    }

    function buildWorkTitle(entry) {
        const role = trimValue(entry.role);
        const company = trimValue(entry.company);

        if (role && company) {
            return `${role} - ${company}`;
        }

        return role || company;
    }

    function buildCertificationTitle(entry) {
        const title = trimValue(entry.title);
        const issuer = trimValue(entry.issuer);

        if (title && issuer) {
            return `${title} - ${issuer}`;
        }

        return title || issuer;
    }

    function getContainer(type) {
        return document.getElementById(sectionConfig[type].containerId);
    }

    function getHiddenInput(type) {
        return document.getElementById(sectionConfig[type].hiddenInputId);
    }

    function createEntryCard(type, values = {}) {
        const template = document.getElementById(sectionConfig[type].templateId);
        const fragment = template.content.cloneNode(true);
        const card = fragment.querySelector("[data-entry-type]");

        sectionConfig[type].fields.forEach((field) => {
            const input = card.querySelector(`[data-field="${field}"]`);
            input.value = values[field] || "";
        });

        return card;
    }

    function ensureEntryCards(type) {
        const container = getContainer(type);
        if (!container.querySelector("[data-entry-type]")) {
            container.appendChild(createEntryCard(type));
        }
    }

    function seedEntries() {
        Object.keys(sectionConfig).forEach((type) => {
            const container = getContainer(type);
            const initialEntries = Array.isArray(initialData[type]) ? initialData[type] : [];

            container.innerHTML = "";
            if (initialEntries.length) {
                initialEntries.forEach((entry) => {
                    container.appendChild(createEntryCard(type, entry));
                });
            } else {
                container.appendChild(createEntryCard(type));
            }
        });
    }

    function collectEntries(type) {
        const container = getContainer(type);
        const cards = [...container.querySelectorAll("[data-entry-type]")];

        return cards
            .map((card) => {
                const entry = {};
                sectionConfig[type].fields.forEach((field) => {
                    entry[field] = trimValue(card.querySelector(`[data-field="${field}"]`).value);
                });
                return entry;
            })
            .filter((entry) => Object.values(entry).some(Boolean));
    }

    function syncStructuredInputs() {
        Object.keys(sectionConfig).forEach((type) => {
            getHiddenInput(type).value = JSON.stringify(collectEntries(type));
        });
    }

    function setTemplate(templateName) {
        const template = templateName || "classic";
        templateInput.value = template;
        previewFrame.dataset.template = template;
        resumeSheet.dataset.template = template;
        previewSummaryTitle.textContent = template === "modern" ? "Profile" : "Summary";

        templateCards.forEach((card) => {
            card.classList.toggle("is-active", card.dataset.templateCard === template);
        });
    }

    function renderHeader() {
        const name = trimValue(document.getElementById("name").value);
        const role = trimValue(document.getElementById("role").value);
        const metaItems = [
            { type: "email", value: trimValue(document.getElementById("email").value) },
            { type: "phone", value: trimValue(document.getElementById("phone").value) },
            { type: "linkedin", value: trimValue(document.getElementById("linkedin").value) },
            { type: "github", value: trimValue(document.getElementById("github").value) },
        ].filter((item) => item.value);

        previewName.textContent = name;
        previewName.hidden = !name;
        previewRole.textContent = role;
        previewRole.hidden = !role;

        previewMeta.innerHTML = "";
        previewContactList.innerHTML = "";
        metaItems.forEach((item) => {
            previewMeta.appendChild(createContactItem(item.type, item.value));
            previewContactList.appendChild(createSidebarContactItem(item.type, item.value));
        });

        previewHeader.hidden = !name && !role && !metaItems.length;
        previewContactSection.hidden = !metaItems.length;
    }

    function renderProfileImage() {
        const imageData = trimValue(profileImageDataInput.value);

        previewProfileImageWrap.hidden = !imageData;
        if (imageData) {
            previewProfileImage.src = imageData;
        } else {
            previewProfileImage.removeAttribute("src");
        }

        if (imageData) {
            formImagePreview.classList.add("has-image");
            formImagePreview.innerHTML = `<img src="${imageData}" alt="Profile preview">`;
        } else {
            formImagePreview.classList.remove("has-image");
            formImagePreview.innerHTML = "<span>No image selected</span>";
        }
    }

    function renderSummarySection() {
        const summary = trimValue(document.getElementById("summary").value);
        previewSummary.textContent = summary;
        previewSummarySection.hidden = !summary;
    }

    function renderEducationSection() {
        const entries = collectEntries("education");
        previewEducationList.innerHTML = "";

        entries.forEach((entry) => {
            const article = document.createElement("article");
            article.className = "resume-item";

            const headline = document.createElement("div");
            headline.className = "resume-item__headline";

            const titleGroup = document.createElement("div");
            titleGroup.className = "resume-item__title-group";

            const title = buildEducationTitle(entry);
            const institution = trimValue(entry.institution);
            const dateText = buildDateText(entry.start_year, entry.end_year);
            const scoreText = trimValue(entry.score);

            if (title) {
                titleGroup.appendChild(createTextElement("h3", "", title));
            }

            if (institution && institution !== title) {
                titleGroup.appendChild(createTextElement("p", "resume-item__subtitle", institution));
            }

            headline.appendChild(titleGroup);

            if (dateText || scoreText) {
                const aside = document.createElement("div");
                aside.className = "resume-item__aside";

                if (dateText) {
                    aside.appendChild(createTextElement("span", "resume-item__date", dateText));
                }

                if (scoreText) {
                    aside.appendChild(createTextElement("span", "resume-item__aside-meta", `CGPA / Score: ${scoreText}`));
                }

                headline.appendChild(aside);
            }

            article.appendChild(headline);

            previewEducationList.appendChild(article);
        });

        previewEducationSection.hidden = !entries.length;
    }

    function renderSkillsSection() {
        const skillGroups = skillFieldIds
            .map((fieldId) => ({
                label: skillFieldLabels[fieldId],
                items: splitSkillItems(document.getElementById(fieldId).value),
            }))
            .filter((group) => group.items.length);

        previewSkillsList.innerHTML = "";

        skillGroups.forEach((group) => {
            const line = document.createElement("p");
            line.className = "skills-group";

            const label = createTextElement("span", "skills-group__label", `${group.label}:`);
            const values = createTextElement("span", "", ` ${group.items.join(", ")}`);

            line.appendChild(label);
            line.appendChild(values);
            previewSkillsList.appendChild(line);
        });

        previewSkillsSection.hidden = !skillGroups.length;
    }

    function renderProjectsSection() {
        const projects = collectEntries("projects");
        previewProjectsList.innerHTML = "";

        projects.forEach((project) => {
            const article = document.createElement("article");
            article.className = "resume-item";

            const headline = document.createElement("div");
            headline.className = "resume-item__headline";

            const titleGroup = document.createElement("div");
            titleGroup.className = "resume-item__title-group";

            if (trimValue(project.title)) {
                titleGroup.appendChild(createTextElement("h3", "", trimValue(project.title)));
            }

            if (trimValue(project.url)) {
                titleGroup.appendChild(createTextElement("p", "resume-item__subtitle", trimValue(project.url)));
            }

            headline.appendChild(titleGroup);
            article.appendChild(headline);

            if (trimValue(project.description)) {
                article.appendChild(createTextElement("p", "", trimValue(project.description)));
            }

            if (trimValue(project.technologies)) {
                article.appendChild(createTextElement("p", "resume-item__meta", `Tech: ${trimValue(project.technologies)}`));
            }

            previewProjectsList.appendChild(article);
        });

        previewProjectsSection.hidden = !projects.length;
    }

    function renderWorkSection() {
        const entries = collectEntries("work_experience");
        previewWorkList.innerHTML = "";

        entries.forEach((entry) => {
            const article = document.createElement("article");
            article.className = "resume-item";

            const headline = document.createElement("div");
            headline.className = "resume-item__headline";

            const titleGroup = document.createElement("div");
            titleGroup.className = "resume-item__title-group";

            const title = buildWorkTitle(entry);
            if (title) {
                titleGroup.appendChild(createTextElement("h3", "", title));
            }

            headline.appendChild(titleGroup);

            const dateText = buildDateText(entry.start_date, entry.end_date);
            if (dateText) {
                headline.appendChild(createTextElement("span", "resume-item__date", dateText));
            }

            article.appendChild(headline);

            if (trimValue(entry.description)) {
                article.appendChild(createTextElement("p", "", trimValue(entry.description)));
            }

            previewWorkList.appendChild(article);
        });

        previewWorkSection.hidden = !entries.length;
    }

    function renderCertificationsSection() {
        const entries = collectEntries("certifications");
        previewCertificationsList.innerHTML = "";

        entries.forEach((entry) => {
            const article = document.createElement("article");
            article.className = "resume-item resume-item--inline";

            const headline = document.createElement("div");
            headline.className = "resume-item__headline";

            const titleGroup = document.createElement("div");
            titleGroup.className = "resume-item__title-group";

            const title = buildCertificationTitle(entry);
            if (title) {
                titleGroup.appendChild(createTextElement("h3", "", title));
            }

            if (trimValue(entry.url)) {
                titleGroup.appendChild(createTextElement("p", "resume-item__subtitle", trimValue(entry.url)));
            }

            headline.appendChild(titleGroup);

            if (trimValue(entry.year)) {
                headline.appendChild(createTextElement("span", "resume-item__date", trimValue(entry.year)));
            }

            article.appendChild(headline);
            previewCertificationsList.appendChild(article);
        });

        previewCertificationsSection.hidden = !entries.length;
    }

    function renderAchievementsSection() {
        const achievements = collectEntries("achievements");
        previewAchievementsList.innerHTML = "";

        achievements.forEach((entry) => {
            previewAchievementsList.appendChild(createTextElement("li", "", trimValue(entry.text)));
        });

        previewAchievementsSection.hidden = !achievements.length;
    }

    function renderCustomSections() {
        const sections = collectEntries("custom_sections");
        previewCustomSections.innerHTML = "";

        sections.forEach((section) => {
            const wrapper = document.createElement("section");
            wrapper.className = "resume-section";

            const title = createTextElement("h2", "", trimValue(section.title) || "Custom Section");
            const content = createTextElement("p", "", trimValue(section.content));

            wrapper.appendChild(title);
            wrapper.appendChild(content);
            previewCustomSections.appendChild(wrapper);
        });
    }

    function getAllSkills() {
        return skillFieldIds.flatMap((fieldId) => splitSkillItems(document.getElementById(fieldId).value));
    }

    function getEntryValues(type, field) {
        return collectEntries(type)
            .map((entry) => trimValue(entry[field]))
            .filter(Boolean);
    }

    function getSectionsPresent() {
        const sections = [];

        if (trimValue(document.getElementById("summary").value)) {
            sections.push("summary");
        }

        if (getAllSkills().length) {
            sections.push("skills");
        }

        Object.keys(sectionConfig).forEach((type) => {
            if (collectEntries(type).length) {
                sections.push(type);
            }
        });

        return sections;
    }

    function renderResultList(target, items, emptyMessage) {
        target.innerHTML = "";

        if (!items.length) {
            target.appendChild(createTextElement("li", "", emptyMessage));
            return;
        }

        items.forEach((item) => {
            target.appendChild(createTextElement("li", "", item));
        });
    }

    function renderBreakdown(items) {
        const breakdownItems = Array.isArray(items)
            ? items.map((item) => `${item.label}: ${item.score}/${item.max_score} - ${item.detail}`)
            : [];

        renderResultList(atsBreakdownList, breakdownItems, "Detailed score breakdown is not available.");
    }

    function getScoreMessage(score) {
        if (score > 80) {
            return `Strong ATS compatibility (${score}/100)`;
        }

        if (score >= 50) {
            return `Moderate ATS compatibility (${score}/100)`;
        }

        return `Low ATS compatibility (${score}/100)`;
    }

    function setScoreColor(score) {
        atsScoreValue.classList.remove("ats-score-badge--high", "ats-score-badge--medium", "ats-score-badge--low", "high-score", "medium-score", "low-score");
        atsScoreStatus.classList.remove("high-score", "medium-score", "low-score");

        if (score > 80) {
            atsScoreValue.classList.add("ats-score-badge--high");
            atsScoreValue.classList.add("high-score");
            atsScoreStatus.classList.add("high-score");
            return;
        }

        if (score >= 50) {
            atsScoreValue.classList.add("ats-score-badge--medium");
            atsScoreValue.classList.add("medium-score");
            atsScoreStatus.classList.add("medium-score");
            return;
        }

        atsScoreValue.classList.add("ats-score-badge--low");
        atsScoreValue.classList.add("low-score");
        atsScoreStatus.classList.add("low-score");
    }

    function renderSuggestions(items) {
        const suggestions = Array.isArray(items) ? [...items] : [];
        suggestions.push("Tip: Tailor your resume for each job role to improve ATS score.");
        renderResultList(atsSuggestionsList, suggestions, "Tip: Tailor your resume for each job role to improve ATS score.");
    }

    function openAtsModal() {
        atsScoreModal.hidden = false;
        document.body.classList.add("modal-open");
    }

    function closeAtsModal() {
        atsScoreModal.hidden = true;
        document.body.classList.remove("modal-open");
    }

    async function handleResumeScore() {
        const payload = {
            role: trimValue(document.getElementById("role").value),
            summary: trimValue(document.getElementById("summary").value),
            skills: getAllSkills(),
            sections: getSectionsPresent(),
            education_count: collectEntries("education").length,
            project_count: collectEntries("projects").length,
            work_experience_count: collectEntries("work_experience").length,
            certification_count: collectEntries("certifications").length,
            achievement_count: collectEntries("achievements").length,
            project_descriptions: getEntryValues("projects", "description"),
            work_descriptions: getEntryValues("work_experience", "description"),
            achievement_texts: getEntryValues("achievements", "text"),
        };

        atsScoreValue.textContent = "Analyzing...";
        atsScoreStatus.textContent = "Reviewing ATS compatibility...";
        atsScoreStatus.classList.remove("high-score", "medium-score", "low-score");
        atsRoleMatch.textContent = "Target role: Analyzing current resume";
        atsScoreValue.classList.remove("ats-score-badge--high", "ats-score-badge--medium", "ats-score-badge--low", "high-score", "medium-score", "low-score");
        renderBreakdown([]);
        renderResultList(atsMissingSkillsList, [], "Reviewing your skills...");
        renderSuggestions([]);
        renderResultList(atsAnalysisNotesList, [], "Reviewing resume depth and keyword usage...");
        openAtsModal();

        try {
            const response = await fetch("/ats_score", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || "Unable to calculate ATS score right now.");
            }

            atsScoreValue.textContent = `${result.score} / 100`;
            atsScoreStatus.textContent = getScoreMessage(result.score);
            atsRoleMatch.textContent = result.matched_role
                ? `Target role: ${result.matched_role}`
                : "Target role: General ATS analysis";
            setScoreColor(result.score);
            renderBreakdown(result.breakdown || []);
            renderResultList(atsMissingSkillsList, result.missing_skills || [], "No major skill gaps found.");
            renderSuggestions(result.suggestions || []);
            renderResultList(atsAnalysisNotesList, result.analysis_notes || [], "No extra analysis notes.");
        } catch (error) {
            atsScoreValue.textContent = "Unavailable";
            atsScoreStatus.textContent = "ATS analysis is currently unavailable.";
            atsRoleMatch.textContent = "Target role: Analysis unavailable";
            atsScoreValue.classList.add("ats-score-badge--low");
            atsScoreValue.classList.add("low-score");
            atsScoreStatus.classList.add("low-score");
            renderBreakdown([]);
            renderResultList(atsMissingSkillsList, [], "Could not complete analysis.");
            renderSuggestions([error.message]);
            renderResultList(atsAnalysisNotesList, [], "Try again after updating your resume.");
        }
    }

    function renderAll() {
        syncStructuredInputs();
        renderHeader();
        renderProfileImage();
        renderSummarySection();
        renderEducationSection();
        renderSkillsSection();
        renderProjectsSection();
        renderWorkSection();
        renderCertificationsSection();
        renderAchievementsSection();
        renderCustomSections();
        setTemplate(templateInput.value);
    }

    templateCards.forEach((card) => {
        card.addEventListener("click", () => {
            setTemplate(card.dataset.templateCard);
            renderAll();
        });
    });

    document.querySelectorAll("[data-add-entry]").forEach((button) => {
        button.addEventListener("click", () => {
            const type = button.dataset.addEntry;
            getContainer(type).appendChild(createEntryCard(type));
            renderAll();
        });
    });

    form.addEventListener("click", (event) => {
        const removeButton = event.target.closest("[data-remove-entry]");
        if (!removeButton) {
            return;
        }

        const card = removeButton.closest("[data-entry-type]");
        const type = card.dataset.entryType;
        card.remove();
        ensureEntryCards(type);
        renderAll();
    });

    form.addEventListener("input", renderAll);
    form.addEventListener("change", renderAll);

    form.addEventListener("submit", () => {
        syncStructuredInputs();
    });

    if (resumeScoreBtn && atsScoreModal) {
        resumeScoreBtn.addEventListener("click", handleResumeScore);

        atsScoreModal.addEventListener("click", (event) => {
            if (event.target.matches("[data-ats-close]")) {
                closeAtsModal();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !atsScoreModal.hidden) {
                closeAtsModal();
            }
        });
    }

    if (profileImageFileInput) {
        profileImageFileInput.addEventListener("change", (event) => {
            const file = event.target.files && event.target.files[0];

            if (!file) {
                profileImageDataInput.value = "";
                renderAll();
                return;
            }

            const reader = new FileReader();
            reader.onload = () => {
                profileImageDataInput.value = typeof reader.result === "string" ? reader.result : "";
                renderAll();
            };
            reader.readAsDataURL(file);
        });
    }

    seedEntries();
    setTemplate(initialData.template || templateInput.value || "classic");
    renderAll();
}
