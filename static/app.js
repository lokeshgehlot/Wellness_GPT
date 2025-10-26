// app.js 
document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    // Global variable to track selected cards and conversation state
    let selectedCards = {
        hospital: null,
        medicine: null,
        lab: null,
        visit_type: null
    };
    
    let currentAgent = "orchestrator";
    let isProcessing = false;

    // Initialize chat
    setTimeout(() => {
        appendMessage("bot", "Hi there! I'm WellnessGPT. How can I help you today?", "orchestrator");
    }, 500);

    // Event listeners
    sendButton.addEventListener("click", sendMessage);
    
    userInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Enable/disable input during processing
    function setInputState(enabled) {
        userInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        isProcessing = !enabled;
        
        if (enabled) {
            userInput.placeholder = "Ask me anything...";
            userInput.focus();
        } else {
            userInput.placeholder = "Processing...";
        }
    }

    async function sendMessage() {
        if (isProcessing) return;
        
        const messageText = userInput.value.trim();
        if (!messageText) return;
    
        appendMessage("user", messageText);
        userInput.value = "";
        setInputState(false);
        
        await processUserMessage(messageText);
        setInputState(true);
    }

    function appendMessage(sender, message, agentType = "orchestrator") {
        if (!message || message.trim() === "") return;
    
        console.log("Appending message - Sender:", sender, "Agent:", agentType);
    
        // Create wrapper for message + avatar
        const messageWrapper = document.createElement("div");
        messageWrapper.classList.add("message-wrapper");
        messageWrapper.classList.add(sender === "bot" ? "bot-wrapper" : "user-wrapper");
    
        // Create avatar
        const avatar = document.createElement("div");
        avatar.classList.add("message-avatar");
        avatar.classList.add(sender === "bot" ? "bot-avatar" : "user-avatar");
        
        // Add icon to avatar (simple sparkle for bot, user icon for user)
        if (sender === "bot") {
            avatar.textContent = "✦";
        } else {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        }
    
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender + "-message");
        
        if (sender === "bot") {
            const agentClass = "agent-" + agentType;
            messageElement.classList.add(agentClass);
            
            const agentBadge = document.createElement("div");
            agentBadge.classList.add("agent-badge");
            const labelText = getAgentLabel(agentType);
            agentBadge.textContent = labelText;
            messageElement.appendChild(agentBadge);
            
            currentAgent = agentType;
        }
    
        const messageContent = document.createElement("span");
        messageContent.classList.add("message-content");
        messageContent.textContent = message;
    
        const messageTime = document.createElement("span");
        messageTime.classList.add("message-time");
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        messageTime.textContent = `${hours}:${minutes}`;
    
        messageElement.appendChild(messageContent);
        messageElement.appendChild(messageTime);
        
        messageWrapper.appendChild(avatar);
        messageWrapper.appendChild(messageElement);
        chatBox.appendChild(messageWrapper);
        
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
    }
    function appendCards(sender, cardsData, messageText = "", agentType = "orchestrator") {
        console.log("Appending cards:", cardsData);
        console.log("Message text:", messageText);
        console.log("Agent type:", agentType);
    
        // Create wrapper for message + avatar
        const messageWrapper = document.createElement("div");
        messageWrapper.classList.add("message-wrapper");
        messageWrapper.classList.add(sender === "bot" ? "bot-wrapper" : "user-wrapper");
    
        // Create avatar for bot messages with cards
        if (sender === "bot") {
            const avatar = document.createElement("div");
            avatar.classList.add("message-avatar", "bot-avatar");
            avatar.textContent = "✦";
            messageWrapper.appendChild(avatar);
        }
    
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender + "-message");
        
        if (sender === "bot") {
            const agentClass = "agent-" + agentType;
            messageElement.classList.add(agentClass);
            
            const agentBadge = document.createElement("div");
            agentBadge.classList.add("agent-badge");
            agentBadge.textContent = getAgentLabel(agentType);
            messageElement.appendChild(agentBadge);
            
            currentAgent = agentType;
        }
    
        const messageContent = document.createElement("span");
        messageContent.classList.add("message-content");
    
        // Add message text if provided
        if (messageText && messageText.trim()) {
            const textElement = document.createElement("div");
            textElement.textContent = messageText.trim();
            textElement.style.marginBottom = "12px";
            messageElement.appendChild(textElement);
        }
    
        // Create cards container
        const cardsContainer = createCardsContainer(cardsData, agentType);
        messageElement.appendChild(cardsContainer);
    
        const messageTime = document.createElement("span");
        messageTime.classList.add("message-time");
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        messageTime.textContent = `${hours}:${minutes}`;
    
        messageElement.appendChild(messageTime);
        
        messageWrapper.appendChild(messageElement);
        chatBox.appendChild(messageWrapper);
        
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
    }

    function appendSuggestedReplies(suggestedReplies, agentType) {
        if (!suggestedReplies || !Array.isArray(suggestedReplies) || suggestedReplies.length === 0) {
            return;
        }
    
        console.log("Appending suggested replies:", suggestedReplies);
        console.log("Current agent context:", agentType);
    
        const repliesContainer = document.createElement("div");
        repliesContainer.classList.add("suggested-replies-container");
        
        // Add a subtle header
        const header = document.createElement("div");
        header.classList.add("suggested-replies-header");
        header.textContent = "Quick questions:";
        repliesContainer.appendChild(header);
    
        const repliesList = document.createElement("div");
        repliesList.classList.add("suggested-replies-list");
    
        suggestedReplies.forEach((reply, index) => {
            const replyButton = document.createElement("button");
            replyButton.classList.add("suggested-reply");
            replyButton.textContent = reply;
            
            // Add agent-specific styling
            if (agentType) {
                replyButton.classList.add(`agent-${agentType}`);
            }
            
            replyButton.addEventListener("click", async function() {
                if (isProcessing) return;
                
                console.log("Suggested reply clicked:", reply);
                console.log("Preserving agent context:", agentType);
                
                // Visual feedback
                replyButton.classList.add("clicked");
                
                // Add the clicked reply as a user message
                appendMessage("user", reply);
                
                // Remove all suggested replies after clicking one
                document.querySelectorAll('.suggested-replies-container').forEach(container => {
                    container.remove();
                });
                
                setInputState(false);
                const typingIndicator = showTypingIndicator();
                
                try {
                    const response = await fetch("/chat", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({ 
                            message: reply,
                            current_agent: agentType,
                            is_suggested_reply: true
                        })
                    });
    
                    removeTypingIndicator(typingIndicator);

                    if (response.ok) {
                        const data = await response.json();
                        await delay(300);
                        
                        // Handle response with cards or regular message
                        if (data.cards && data.cards.length > 0) {
                            appendCards("bot", data.cards, data.response, data.agent);
                        } else {
                            appendMessage("bot", data.response, data.agent);
                        }
                        
                        // Show new suggestions if provided
                        if (data.suggested_replies && data.suggested_replies.length > 0) {
                            await delay(500);
                            appendSuggestedReplies(data.suggested_replies, data.agent);
                        }
                    } else {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                } catch (error) {
                    console.error("Error:", error);
                    removeTypingIndicator(typingIndicator);
                    appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
                } finally {
                    setInputState(true);
                }
            });
    
            repliesList.appendChild(replyButton);
        });
    
        repliesContainer.appendChild(repliesList);
        
        // Add to chat box
        chatBox.appendChild(repliesContainer);
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
    }

    function createCardsContainer(cardsData, agentType) {
        console.log("Creating cards container with", cardsData.length, "cards");
        
        const cardsContainer = document.createElement("div");
        cardsContainer.classList.add("cards-container");

        cardsData.forEach((card, index) => {
            const cardElement = document.createElement("div");
            cardElement.classList.add("message-card");
            
            // Handle different card types
            if (card.type === "hospital" || card.type === "hospital_selection") {
                cardElement.classList.add("hospital-card");
                createHospitalCard(cardElement, card);
            } else if (card.type === "medicine") {
                cardElement.classList.add("medicine-card", card.status);
                createMedicineCard(cardElement, card);
            } else if (card.type === "prescription_medicine") {
                cardElement.classList.add("prescription-medicine-card", card.status);
                createPrescriptionMedicineCard(cardElement, card);
            } else if (card.type === "booking_confirmation") {
                cardElement.classList.add("booking-confirmation-card");
                createBookingConfirmationCard(cardElement, card);
            } else if (card.type === "test_booking_confirmation") {
                cardElement.classList.add("test-booking-confirmation-card");
                createTestBookingConfirmationCard(cardElement, card);
            } else if (card.type === "lab" || card.type === "lab_selection") {
                cardElement.classList.add("lab-card", "card-lab_selection");
                createLabCard(cardElement, card);
            } else if (card.type === "test_package") {  // NEW
                cardElement.classList.add("test-package-card", "card-test_package");
                createTestPackageCard(cardElement, card);
            } else if (card.type === "visit_type") {
                cardElement.classList.add("visit-type-card");
                createVisitTypeCard(cardElement, card);
            } else if (card.type === "lab_booking_confirmation") {  // NEW
                cardElement.classList.add("lab-booking-confirmation-card");
                createLabBookingConfirmationCard(cardElement, card);
            } else if (card.type === "quick_reply") {
                cardElement.classList.add("quick-reply-card");
                createQuickReplyCard(cardElement, card);
            } else {
                // Default card creation
                createGenericCard(cardElement, card);
            }

            cardsContainer.appendChild(cardElement);
        });

        console.log("Cards container created with", cardsContainer.children.length, "cards");
        return cardsContainer;
    }
    function createLabCard(cardElement, card) {
        console.log("Creating lab card:", card);
        
        // Add card content
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }
    
        if (card.description) {
            const descElement = document.createElement("div");
            descElement.classList.add("card-description");
            descElement.textContent = card.description;
            cardElement.appendChild(descElement);
        }
    
        // Add tests available
        if (card.tests_available && Array.isArray(card.tests_available)) {
            const testsElement = document.createElement("div");
            testsElement.classList.add("lab-tests");
            testsElement.innerHTML = `<strong>Tests Available:</strong> ${card.tests_available.join(', ')}`;
            cardElement.appendChild(testsElement);
        }
    
        if (card.meta) {
            const metaElement = document.createElement("div");
            metaElement.classList.add("card-meta");
            metaElement.innerHTML = card.meta;
            cardElement.appendChild(metaElement);
        }
    
        // Add click handler for lab cards
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            console.log(`Lab card clicked:`, card.title);
            
            // Remove selected class from all lab cards
            document.querySelectorAll('.lab-card').forEach(cardEl => {
                cardEl.classList.remove('selected');
            });
            
            // Add selected class to clicked card
            cardElement.classList.add('selected');
            
            const selectionText = card.selection_text || card.title;
            appendMessage("user", selectionText);
            
            setInputState(false);
            const typingIndicator = showTypingIndicator();
            
            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        message: selectionText,
                        card_data: card 
                    })
                });
    
                removeTypingIndicator(typingIndicator);
    
                if (response.ok) {
                    const data = await response.json();
                    await delay(300);
                    
                    if (data.cards && data.cards.length > 0) {
                        appendCards("bot", data.cards, data.response, data.agent);
                    } else {
                        appendMessage("bot", data.response, data.agent);
                    }
                    
                    // Show suggestions if available
                    if (data.suggested_replies && data.suggested_replies.length > 0) {
                        await delay(500);
                        appendSuggestedReplies(data.suggested_replies, data.agent);
                    }
                }
            } catch (error) {
                console.error("Error:", error);
                removeTypingIndicator(typingIndicator);
                appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
            } finally {
                setInputState(true);
            }
        });
    }
    
    function createVisitTypeCard(cardElement, card) {
        console.log("Creating visit type card:", card);
        
        // Add card content
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }
    
        if (card.description) {
            const descElement = document.createElement("div");
            descElement.classList.add("card-description");
            descElement.textContent = card.description;
            cardElement.appendChild(descElement);
        }
    
        if (card.meta) {
            const metaElement = document.createElement("div");
            metaElement.classList.add("card-meta");
            metaElement.innerHTML = card.meta;
            cardElement.appendChild(metaElement);
        }
    
        // Add click handler for visit type cards
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            console.log(`Visit type card clicked:`, card.title);
            
            // Remove selected class from all visit type cards
            document.querySelectorAll('.visit-type-card').forEach(cardEl => {
                cardEl.classList.remove('selected');
            });
            
            // Add selected class to clicked card
            cardElement.classList.add('selected');
            
            const selectionText = card.selection_text || card.title;
            appendMessage("user", selectionText);
            
            setInputState(false);
            const typingIndicator = showTypingIndicator();
            
            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        message: selectionText,
                        card_data: card 
                    })
                });
    
                removeTypingIndicator(typingIndicator);
    
                if (response.ok) {
                    const data = await response.json();
                    await delay(300);
                    
                    if (data.cards && data.cards.length > 0) {
                        appendCards("bot", data.cards, data.response, data.agent);
                    } else {
                        appendMessage("bot", data.response, data.agent);
                    }
                    
                    // Show suggestions if available
                    if (data.suggested_replies && data.suggested_replies.length > 0) {
                        await delay(500);
                        appendSuggestedReplies(data.suggested_replies, data.agent);
                    }
                }
            } catch (error) {
                console.error("Error:", error);
                removeTypingIndicator(typingIndicator);
                appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
            } finally {
                setInputState(true);
            }
        });
    }
    
    // Test Package Card Creation
    function createTestPackageCard(cardElement, card) {
        console.log("Creating test package card:", card);
        
        // Package title
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.style.fontSize = "16px";
            titleElement.style.fontWeight = "600";
            titleElement.style.color = "#5e35b1";
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }
        
        // Subtitle (price and parameters)
        if (card.subtitle) {
            const subtitleElement = document.createElement("div");
            subtitleElement.classList.add("card-subtitle");
            subtitleElement.style.fontSize = "14px";
            subtitleElement.style.color = "#666";
            subtitleElement.style.marginTop = "4px";
            subtitleElement.textContent = card.subtitle;
            cardElement.appendChild(subtitleElement);
        }
        
        // Package details
        if (card.details && Array.isArray(card.details)) {
            const detailsContainer = document.createElement("div");
            detailsContainer.style.marginTop = "12px";
            detailsContainer.style.fontSize = "13px";
            detailsContainer.style.color = "#555";
            
            card.details.forEach(detail => {
                const detailLine = document.createElement("div");
                detailLine.style.marginBottom = "4px";
                detailLine.textContent = detail;
                detailsContainer.appendChild(detailLine);
            });
            
            cardElement.appendChild(detailsContainer);
        }
        
        // Recommended badge
        if (card.recommended) {
            const badge = document.createElement("div");
            badge.style.cssText = "display: inline-block; background: #ffd700; color: #000; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-top: 8px;";
            badge.textContent = "⭐ Recommended";
            cardElement.appendChild(badge);
        }
        
        // Add click handler for test package cards
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            console.log(`Test package card clicked:`, card.title);
            
            // Remove selected class from all test package cards
            document.querySelectorAll('.test-package-card').forEach(cardEl => {
                cardEl.classList.remove('selected');
            });
            
            // Add selected class to clicked card
            cardElement.classList.add('selected');
            
            const selectionText = `I want the ${card.title}`;
            appendMessage("user", selectionText);
            
            setInputState(false);
            const typingIndicator = showTypingIndicator();
            
            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        message: selectionText,
                        card_data: card 
                    })
                });
    
                removeTypingIndicator(typingIndicator);
    
                if (response.ok) {
                    const data = await response.json();
                    await delay(300);
                    
                    if (data.cards && data.cards.length > 0) {
                        appendCards("bot", data.cards, data.response, data.agent);
                    } else {
                        appendMessage("bot", data.response, data.agent);
                    }
                    
                    if (data.suggested_replies && data.suggested_replies.length > 0) {
                        appendSuggestedReplies(data.suggested_replies, data.agent);
                    }
                }
            } catch (error) {
                console.error("Error:", error);
                removeTypingIndicator(typingIndicator);
                appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
            } finally {
                setInputState(true);
            }
        });
    }
    
    // Lab Booking Confirmation Card
    function createLabBookingConfirmationCard(cardElement, card) {
        console.log("Creating lab booking confirmation card:", card);
        
        // Remove click handler for confirmation cards
        cardElement.style.cursor = "default";
        
        // Confirmation header with icon
        const header = document.createElement("div");
        header.style.cssText = "display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e0f2f1;";
        header.innerHTML = `
            <div style="width: 32px; height: 32px; background: #26a69a; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;">
                🔬
            </div>
            <div style="font-size: 18px; font-weight: 600; color: #26a69a;">
                ${card.title || "Lab Test Booked Successfully"}
            </div>
        `;
        cardElement.appendChild(header);
        
        // Booking ID
        if (card.booking_id) {
            const bookingId = document.createElement("div");
            bookingId.style.cssText = "background: #e0f2f1; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; border-left: 3px solid #26a69a;";
            bookingId.innerHTML = `<strong>Booking ID:</strong> ${card.booking_id}`;
            cardElement.appendChild(bookingId);
        }
        
        // Booking details
        if (card.details && Array.isArray(card.details)) {
            const detailsSection = document.createElement("div");
            detailsSection.style.marginBottom = "16px";
            
            const detailsTitle = document.createElement("div");
            detailsTitle.style.cssText = "font-size: 15px; font-weight: 600; color: #333; margin-bottom: 10px;";
            detailsTitle.textContent = "Booking Details";
            detailsSection.appendChild(detailsTitle);
            
            card.details.forEach(detail => {
                const detailItem = document.createElement("div");
                detailItem.style.cssText = "padding: 6px 0; font-size: 14px; color: #555; border-bottom: 1px solid #f5f5f5;";
                detailItem.textContent = detail;
                detailsSection.appendChild(detailItem);
            });
            
            cardElement.appendChild(detailsSection);
        }
        
        // Next steps
        if (card.next_steps && Array.isArray(card.next_steps)) {
            const stepsSection = document.createElement("div");
            stepsSection.style.cssText = "background: #f5f5f5; padding: 14px; border-radius: 8px;";
            
            const stepsTitle = document.createElement("div");
            stepsTitle.style.cssText = "font-size: 14px; font-weight: 600; color: #555; margin-bottom: 10px;";
            stepsTitle.textContent = "Next Steps:";
            stepsSection.appendChild(stepsTitle);
            
            card.next_steps.forEach((step, index) => {
                const stepItem = document.createElement("div");
                stepItem.style.cssText = "font-size: 13px; color: #666; margin: 6px 0; padding-left: 20px; position: relative;";
                stepItem.innerHTML = `<span style="position: absolute; left: 0; color: #26a69a;">${index + 1}.</span> ${step}`;
                stepsSection.appendChild(stepItem);
            });
            
            cardElement.appendChild(stepsSection);
        }
    }
    
    function createTestBookingConfirmationCard(cardElement, card) {
        console.log("Creating test booking confirmation card:", card);
        
        // Add header with icon and title
        const headerElement = document.createElement("div");
        headerElement.classList.add("booking-header", "test-booking-header");
        
        const iconElement = document.createElement("div");
        iconElement.classList.add("booking-icon", "test-icon");
        iconElement.textContent = "🩺";
        headerElement.appendChild(iconElement);
    
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("booking-title");
            titleElement.textContent = card.title;
            headerElement.appendChild(titleElement);
        }
        
        cardElement.appendChild(headerElement);
    
        // Add booking ID
        if (card.booking_id) {
            const idElement = document.createElement("div");
            idElement.classList.add("booking-id");
            idElement.innerHTML = `<strong>Booking ID:</strong> ${card.booking_id}`;
            cardElement.appendChild(idElement);
        }
    
        // Add comprehensive details section
        if (card.details) {
            const detailsElement = document.createElement("div");
            detailsElement.classList.add("booking-details", "test-details");
            
            const detailsTitle = document.createElement("div");
            detailsTitle.classList.add("details-title");
            detailsTitle.textContent = "Test Booking Details";
            detailsElement.appendChild(detailsTitle);
            
            Object.entries(card.details).forEach(([key, value]) => {
                const detailRow = document.createElement("div");
                detailRow.classList.add("detail-row");
                detailRow.innerHTML = `
                    <span class="detail-label">${key}:</span> 
                    <span class="detail-value">${value}</span>`;
                detailsElement.appendChild(detailRow);
            });
            
            cardElement.appendChild(detailsElement);
        }
    
        // Add instructions
        if (card.instructions && Array.isArray(card.instructions)) {
            const instructionsElement = document.createElement("div");
            instructionsElement.classList.add("booking-instructions", "test-instructions");
            
            const instructionsTitle = document.createElement("div");
            instructionsTitle.classList.add("instructions-title");
            instructionsTitle.textContent = "Important Instructions:";
            instructionsElement.appendChild(instructionsTitle);
            
            card.instructions.forEach(instruction => {
                const instructionItem = document.createElement("div");
                instructionItem.classList.add("instruction-item");
                instructionItem.textContent = instruction;
                instructionsElement.appendChild(instructionItem);
            });
            
            cardElement.appendChild(instructionsElement);
        }
    
        // Add confirmation message
        const messageElement = document.createElement("div");
        messageElement.classList.add("confirmation-message");
        messageElement.textContent = "You'll receive a confirmation message with detailed instructions.";
        cardElement.appendChild(messageElement);
        
        // Clear selections when booking is confirmed
        clearCardSelections();
    }
    function createHospitalCard(cardElement, card) {
        // Add card content
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }

        if (card.description) {
            const descElement = document.createElement("div");
            descElement.classList.add("card-description");
            descElement.textContent = card.description;
            cardElement.appendChild(descElement);
        }

        if (card.meta) {
            const metaElement = document.createElement("div");
            metaElement.classList.add("card-meta");
            metaElement.innerHTML = card.meta;
            cardElement.appendChild(metaElement);
        }

        // Add click handler for hospital cards
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            const cardType = card.type;
            const cardId = card.hospital_id;
            
            console.log(`Hospital card clicked:`, card.title);
            
            // Remove selected class from all hospital cards
            document.querySelectorAll(`.${cardType}-card`).forEach(cardEl => {
                cardEl.classList.remove('selected');
            });
            
            // Toggle selection
            if (selectedCards[cardType] === cardId) {
                cardElement.classList.remove('selected');
                selectedCards[cardType] = null;
                console.log(`Hospital deselected:`, card.title);
                return;
            } else {
                cardElement.classList.add('selected');
                selectedCards[cardType] = cardId;
                console.log(`Hospital selected:`, card.title);
                
                const selectionText = card.selection_text || card.title;
                appendMessage("user", selectionText);
                
                setInputState(false);
                const typingIndicator = showTypingIndicator();
                
                try {
                    const response = await fetch("/chat", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({ 
                            message: selectionText,
                            card_data: card 
                        })
                    });

                    removeTypingIndicator(typingIndicator);

                    if (response.ok) {
                        const data = await response.json();
                        await delay(300);
                        
                        if (data.cards && data.cards.length > 0) {
                            appendCards("bot", data.cards, data.response, data.agent);
                        } else {
                            appendMessage("bot", data.response, data.agent);
                            
                            // Clear selections when appointment is confirmed
                            if (data.response.toLowerCase().includes("appointment id") || 
                                data.response.toLowerCase().includes("confirmed")) {
                                clearCardSelections();
                            }
                        }
                        
                        // Show suggestions if available
                        if (data.suggested_replies && data.suggested_replies.length > 0) {
                            await delay(500);
                            appendSuggestedReplies(data.suggested_replies, data.agent);
                        }
                    }
                } catch (error) {
                    console.error("Error:", error);
                    removeTypingIndicator(typingIndicator);
                    appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
                } finally {
                    setInputState(true);
                }
            }
        });
    }

    function createGenericCard(cardElement, card) {
        // Add basic card content
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }

        if (card.description) {
            const descElement = document.createElement("div");
            descElement.classList.add("card-description");
            descElement.textContent = card.description;
            cardElement.appendChild(descElement);
        }

        if (card.meta) {
            const metaElement = document.createElement("div");
            metaElement.classList.add("card-meta");
            metaElement.innerHTML = card.meta;
            cardElement.appendChild(metaElement);
        }
    }

    function createQuickReplyCard(cardElement, card) {
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.classList.add("card-title");
            titleElement.textContent = card.title;
            cardElement.appendChild(titleElement);
        }

        // Quick reply cards are clickable
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            const selectionText = card.selection_text || card.title;
            appendMessage("user", selectionText);
            
            setInputState(false);
            const typingIndicator = showTypingIndicator();
            
            try {
                await processUserMessage(selectionText);
            } finally {
                removeTypingIndicator(typingIndicator);
                setInputState(true);
            }
        });
    }

    function createPrescriptionMedicineCard(cardElement, card) {
        console.log("Creating prescription medicine card:", card);
        
        const prescriptionContent = document.createElement("div");
        prescriptionContent.classList.add("prescription-content");
        
        // Medicine header with name and strength
        const headerElement = document.createElement("div");
        headerElement.classList.add("prescription-header");
        
        const nameElement = document.createElement("div");
        nameElement.classList.add("prescription-name");
        nameElement.textContent = `${card.medicine_name} ${card.strength || ''}`.trim();
        headerElement.appendChild(nameElement);
        
        // Status badge
        const statusElement = document.createElement("div");
        statusElement.classList.add("prescription-status", `status-${card.status}`);
        statusElement.textContent = card.status === 'available' ? 'Available' : 'Unavailable';
        headerElement.appendChild(statusElement);
        
        prescriptionContent.appendChild(headerElement);
        
        // Dosage and instructions
        if (card.dosage || card.instructions) {
            const dosageElement = document.createElement("div");
            dosageElement.classList.add("prescription-dosage");
            
            if (card.dosage) {
                const dosageText = document.createElement("div");
                dosageText.classList.add("dosage-text");
                dosageText.innerHTML = `<strong>Dosage:</strong> ${card.dosage}`;
                dosageElement.appendChild(dosageText);
            }
            
            if (card.instructions) {
                const instructionsText = document.createElement("div");
                instructionsText.classList.add("instructions-text");
                instructionsText.innerHTML = `<strong>Instructions:</strong> ${card.instructions}`;
                dosageElement.appendChild(instructionsText);
            }
            
            prescriptionContent.appendChild(dosageElement);
        }
        
        // Duration and purpose
        if (card.duration || card.purpose) {
            const detailsElement = document.createElement("div");
            detailsElement.classList.add("prescription-details");
            
            if (card.duration) {
                const durationText = document.createElement("div");
                durationText.innerHTML = `<strong>Duration:</strong> ${card.duration}`;
                detailsElement.appendChild(durationText);
            }
            
            if (card.purpose) {
                const purposeText = document.createElement("div");
                purposeText.innerHTML = `<strong>Purpose:</strong> ${card.purpose}`;
                detailsElement.appendChild(purposeText);
            }
            
            prescriptionContent.appendChild(detailsElement);
        }
        
        // Prescriber information
        if (card.prescriber) {
            const prescriberElement = document.createElement("div");
            prescriberElement.classList.add("prescriber-info");
            prescriberElement.innerHTML = `<strong>Prescribed by:</strong> ${card.prescriber}`;
            prescriptionContent.appendChild(prescriberElement);
        }
        
        // Refills remaining
        if (card.refills_remaining !== undefined) {
            const refillsElement = document.createElement("div");
            refillsElement.classList.add("refills-info");
            refillsElement.innerHTML = `<strong>Refills remaining:</strong> ${card.refills_remaining}`;
            prescriptionContent.appendChild(refillsElement);
        }
        
        // Price
        if (card.price) {
            const priceElement = document.createElement("div");
            priceElement.classList.add("prescription-price");
            priceElement.innerHTML = `<strong>Price:</strong> ${card.price}`;
            prescriptionContent.appendChild(priceElement);
        }
        
        // Prescription requirement
        if (card.prescription_required !== undefined) {
            const rxElement = document.createElement("div");
            rxElement.classList.add("prescription-required");
            rxElement.innerHTML = `<strong>Prescription:</strong> ${card.prescription_required ? 'Required' : 'Not required'}`;
            prescriptionContent.appendChild(rxElement);
        }
        
        // Action buttons
        if (card.actions && Array.isArray(card.actions)) {
            const actionsElement = document.createElement("div");
            actionsElement.classList.add("prescription-actions");
            
            card.actions.forEach(action => {
                const actionButton = document.createElement("button");
                actionButton.classList.add("prescription-action", `action-${action.type}`);
                actionButton.textContent = action.text;
                
                actionButton.addEventListener("click", async function(e) {
                    e.stopPropagation();
                    if (isProcessing) return;
                    
                    console.log(`Action clicked: ${action.type} for ${card.medicine_name}`);
                    
                    let selectionText;
                    if (action.type === "add_to_cart") {
                        selectionText = `Add ${card.medicine_name} to cart`;
                    } else if (action.type === "find_alternatives") {
                        selectionText = `Find alternatives for ${card.medicine_name}`;
                    } else if (action.type === "view_generics") {
                        selectionText = `Show generic alternatives for ${card.medicine_name}`;
                    } else {
                        selectionText = action.text;
                    }
                    
                    appendMessage("user", selectionText);
                    
                    setInputState(false);
                    const typingIndicator = showTypingIndicator();
                    
                    try {
                        await processUserMessage(selectionText);
                    } finally {
                        removeTypingIndicator(typingIndicator);
                        setInputState(true);
                    }
                });
                
                actionsElement.appendChild(actionButton);
            });
            
            prescriptionContent.appendChild(actionsElement);
        }
        
        cardElement.appendChild(prescriptionContent);
    }

    function createMedicineCard(cardElement, card) {
        console.log("Creating medicine card:", card);
        
        const medicineContent = document.createElement("div");
        medicineContent.classList.add("medicine-content");
        
        // Medicine image
        const imageElement = document.createElement("img");
        imageElement.classList.add("medicine-image");
        imageElement.src = card.image_url || "/static/images/medicine/medicine-placeholder.jpg";
        imageElement.alt = card.medicine_name;
        imageElement.onerror = function() {
            this.src = "/static/images/medicine/medicine-placeholder.jpg";
        };
        medicineContent.appendChild(imageElement);
        
        // Medicine info
        const infoElement = document.createElement("div");
        infoElement.classList.add("medicine-info");
        
        // Medicine name and status
        const nameElement = document.createElement("div");
        nameElement.classList.add("medicine-name");
        nameElement.textContent = card.medicine_name;
        infoElement.appendChild(nameElement);
        
        const statusElement = document.createElement("div");
        statusElement.classList.add("medicine-status", `status-${card.status}`);
        statusElement.textContent = card.status === 'available' ? 'Available' : 'Unavailable';
        infoElement.appendChild(statusElement);
        
        // Medicine price
        const priceElement = document.createElement("div");
        priceElement.classList.add("medicine-price");
        priceElement.textContent = card.price || "Price not available";
        infoElement.appendChild(priceElement);
        
        // Medicine description
        if (card.description) {
            const descElement = document.createElement("div");
            descElement.classList.add("medicine-description");
            descElement.textContent = card.description;
            infoElement.appendChild(descElement);
        }
        
        // Alternatives (for unavailable medicines)
        if (card.alternatives && card.alternatives.length > 0) {
            const alternativesElement = document.createElement("div");
            alternativesElement.classList.add("medicine-alternatives");
            alternativesElement.innerHTML = `<strong>Alternatives:</strong> ${card.alternatives.join(', ')}`;
            infoElement.appendChild(alternativesElement);
        }
        
        medicineContent.appendChild(infoElement);
        cardElement.appendChild(medicineContent);
        
        // Add click handler for medicine cards
        cardElement.addEventListener("click", async function() {
            if (isProcessing) return;
            
            console.log(`Medicine card clicked:`, card.medicine_name);
            
            const selectionText = `I want to order ${card.medicine_name}`;
            appendMessage("user", selectionText);
            
            setInputState(false);
            const typingIndicator = showTypingIndicator();
            
            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        message: selectionText,
                        card_data: card 
                    })
                });

                removeTypingIndicator(typingIndicator);

                if (response.ok) {
                    const data = await response.json();
                    await delay(300);
                    
                    if (data.cards && data.cards.length > 0) {
                        appendCards("bot", data.cards, data.response, data.agent);
                    } else {
                        appendMessage("bot", data.response, data.agent);
                    }
                    
                    // Show suggestions if available
                    if (data.suggested_replies && data.suggested_replies.length > 0) {
                        await delay(500);
                        appendSuggestedReplies(data.suggested_replies, data.agent);
                    }
                }
            } catch (error) {
                console.error("Error:", error);
                removeTypingIndicator(typingIndicator);
                appendMessage("bot", "Sorry, I'm having trouble. Please try again.", "orchestrator");
            } finally {
                setInputState(true);
            }
        });
    }

    function createBookingConfirmationCard(cardElement, card) {
        console.log("Creating booking confirmation card:", card);
        
        // Add header with icon and title
        const headerElement = document.createElement("div");
        headerElement.classList.add("booking-header");
        headerElement.style.cssText = "display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e0f2f1;";
        
        const iconElement = document.createElement("div");
        iconElement.style.cssText = "width: 32px; height: 32px; background: #4CAF50; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;";
        iconElement.textContent = "✓"; // Add checkmark icon
        headerElement.appendChild(iconElement);
    
        if (card.title) {
            const titleElement = document.createElement("div");
            titleElement.style.cssText = "font-size: 18px; font-weight: 600; color: #4CAF50;";
            titleElement.textContent = card.title;
            headerElement.appendChild(titleElement);
        }
        
        cardElement.appendChild(headerElement);
    
        // Add appointment ID with duration
        if (card.appointment_id) {
            const idElement = document.createElement("div");
            idElement.style.cssText = "background: #e8f5e8; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; border-left: 3px solid #4CAF50;";
            idElement.innerHTML = `<strong>Appointment ID:</strong> ${card.appointment_id}`;
            cardElement.appendChild(idElement);
        }
    
        // Add comprehensive details section
        if (card.details) {
            const detailsElement = document.createElement("div");
            detailsElement.style.marginBottom = "16px";
            
            const detailsTitle = document.createElement("div");
            detailsTitle.style.cssText = "font-size: 15px; font-weight: 600; color: #333; margin-bottom: 10px;";
            detailsTitle.textContent = "Appointment Details";
            detailsElement.appendChild(detailsTitle);
            
            Object.entries(card.details).forEach(([key, value]) => {
                const detailRow = document.createElement("div");
                detailRow.style.cssText = "padding: 6px 0; font-size: 14px; color: #555; border-bottom: 1px solid #f5f5f5;";
                detailRow.innerHTML = `<strong>${key}:</strong> ${value}`;
                detailsElement.appendChild(detailRow);
            });
            
            cardElement.appendChild(detailsElement);
        }
    
        // Add instructions
        if (card.instructions && Array.isArray(card.instructions)) {
            const instructionsElement = document.createElement("div");
            instructionsElement.style.cssText = "background: #f5f5f5; padding: 14px; border-radius: 8px; margin-bottom: 16px;";
            
            const instructionsTitle = document.createElement("div");
            instructionsTitle.style.cssText = "font-size: 14px; font-weight: 600; color: #555; margin-bottom: 10px;";
            instructionsTitle.textContent = "Important Instructions:";
            instructionsElement.appendChild(instructionsTitle);
            
            card.instructions.forEach((instruction, index) => {
                const instructionItem = document.createElement("div");
                instructionItem.style.cssText = "font-size: 13px; color: #666; margin: 6px 0; padding-left: 20px; position: relative;";
                instructionItem.innerHTML = `<span style="position: absolute; left: 0; color: #4CAF50;">${index + 1}.</span> ${instruction}`;
                instructionsElement.appendChild(instructionItem);
            });
            
            cardElement.appendChild(instructionsElement);
        }
    
        // Add confirmation message
        const messageElement = document.createElement("div");
        messageElement.style.cssText = "font-size: 13px; color: #666; font-style: italic; text-align: center; padding: 10px;";
        messageElement.textContent = "You'll receive a confirmation message shortly.";
        cardElement.appendChild(messageElement);
        
        // Clear selections when booking is confirmed
        clearCardSelections();
    }

    async function processUserMessage(messageText) {
        const typingIndicator = showTypingIndicator();
        
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ message: messageText })
            });
    
            removeTypingIndicator(typingIndicator);
    
            if (response.ok) {
                const data = await response.json();
                await delay(300);
                
                if (data.cards && data.cards.length > 0) {
                    appendCards("bot", data.cards, data.response, data.agent);
                } else {
                    appendMessage("bot", data.response, data.agent);
                }
                
                // Show new suggestions if provided
                if (data.suggested_replies && data.suggested_replies.length > 0) {
                    await delay(500);
                    appendSuggestedReplies(data.suggested_replies, data.agent);
                }
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error("Error:", error);
            removeTypingIndicator(typingIndicator);
            appendMessage("bot", "Sorry, I'm having trouble connecting to the server. Please check your connection and try again.", "orchestrator");
        }
    }
    
    // Function to clear card selections
    function clearCardSelections() {
        selectedCards = {
            hospital: null,
            medicine: null,
            lab: null,
            visit_type: null
        };
        
        // Remove selected class from all cards
        document.querySelectorAll('.message-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        console.log("Card selections cleared");
    }

    function getAgentLabel(agentType) {
        const labels = {
            "orchestrator": "Health Assistant",
            "symptom": "Symptom Triage Agent",
            "care_plan": "Care Plan Agent",
            "policy_analysis": "Insurance Advisor Agent",
            "scheduling": "Scheduling Agent",
            "pharmacy": "E-Pharmacy Agent",
            "lab_test": "Lab Test Specialist" 
        };
        return labels[agentType] || "Health Assistant";
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.classList.add("message", "bot-message", "typing-indicator");
        typingDiv.id = "typing-indicator";
        
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        chatBox.appendChild(typingDiv);
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
        
        return typingDiv;
    }

    function removeTypingIndicator(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Initialize
    userInput.focus();
    setInputState(true);
    
    // Add error handling for network issues
    window.addEventListener('online', () => {
        console.log('Network connection restored');
    });
    
    window.addEventListener('offline', () => {
        appendMessage("bot", "Network connection lost. Please check your internet connection.", "orchestrator");
    });
});