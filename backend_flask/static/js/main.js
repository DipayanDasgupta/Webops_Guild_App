// --- Globals and State ---
let isDarkMode = localStorage.getItem('darkMode') === 'true';
let currentUploadedFileObject = null; // Stores the actual File object for the current image context
let currentImagePreviewUrl = null;    // Stores the URL (can be dataURL or server URL) for the displayed preview
let currentRecommendations = [];    // Always holds the latest valid recommendation set
let cartItems = [];
let wishlistItems = [];
let detailedProductToShow = null;
let loggedInUser = null;

const API_BASE_URL = '';

// --- DOM Elements (ensure all are defined and correctly ID'd in index.html) ---
const userAuthSection = document.getElementById('userAuthSection');
const loginModal = document.getElementById('loginModal');
const signupModal = document.getElementById('signupModal');
const closeLoginModalBtn = document.getElementById('closeLoginModalBtn');
const closeSignupModalBtn = document.getElementById('closeSignupModalBtn');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const switchToSignupBtn = document.getElementById('switchToSignupBtn');
const switchToLoginBtn = document.getElementById('switchToLoginBtn');
const darkModeToggle = document.getElementById('darkModeToggle');
const darkModeIcon = document.getElementById('darkModeIcon');
const imageFileInput = document.getElementById('imageFile');
const imagePreview = document.getElementById('imagePreview');
const imagePreviewPlaceholder = document.getElementById('imagePreviewPlaceholder');
const promptForm = document.getElementById('promptForm');
const promptInput = document.getElementById('promptInput');
const clearPromptBtn = document.getElementById('clearPromptBtn');
const sendPromptBtn = document.getElementById('sendPromptBtn');
const examplePromptsList = document.getElementById('examplePromptsList');
const aiInsightsSection = document.getElementById('aiInsightsSection');
const openaiDescriptionText = document.getElementById('openaiDescriptionText');
const geminiRefinementText = document.getElementById('geminiRefinementText');
const loadingText = document.getElementById('loadingText');
const noRecommendationsText = document.getElementById('noRecommendationsText');
const initialMessage = document.getElementById('initialMessage');
const recommendationGrid = document.getElementById('recommendationGrid');
const wishlistSection = document.getElementById('wishlistSection');
const wishlistCount = document.getElementById('wishlistCount');
const emptyWishlistMessage = document.getElementById('emptyWishlistMessage');
const wishlistItemsList = document.getElementById('wishlistItemsList');
const checkoutSection = document.getElementById('checkoutSection');
const cartItemCountHeader = document.getElementById('cartItemCountHeader');
const emptyCartMessage = document.getElementById('emptyCartMessage');
const cartContents = document.getElementById('cartContents');
const cartItemCount = document.getElementById('cartItemCount');
const cartItemsList = document.getElementById('cartItemsList');
const cartTotal = document.getElementById('cartTotal');
const cartTotalPrice = document.getElementById('cartTotalPrice');
const proceedToCheckoutBtn = document.getElementById('proceedToCheckoutBtn');
const productModalOverlay = document.getElementById('productModalOverlay');
const productModalCloseBtn = document.getElementById('productModalCloseBtn');
const modalMainImage = document.getElementById('modalMainImage');
const modalThumbnails = document.getElementById('modalThumbnails');
const modalProductName = document.getElementById('modalProductName');
const modalProductPrice = document.getElementById('modalProductPrice');
const modalProductDescription = document.getElementById('modalProductDescription');
const modalProductAttributes = document.getElementById('modalProductAttributes');
const modalRecommendationReason = document.getElementById('modalRecommendationReason');
const modalReasonText = document.getElementById('modalReasonText');
const modalDetailedReasonsList = document.getElementById('modalDetailedReasonsList');
const modalToggleWishlistBtn = document.getElementById('modalToggleWishlistBtn');
const modalWishlistBtnText = document.getElementById('modalWishlistBtnText');
const modalToggleCartBtn = document.getElementById('modalToggleCartBtn');
const modalCartBtnText = document.getElementById('modalCartBtnText');

// --- Utility Functions ---
function showLoading(isLoading) {
    if(loadingText) loadingText.style.display = isLoading ? 'flex' : 'none';
    if(sendPromptBtn) sendPromptBtn.disabled = isLoading;
    if(imageFileInput) imageFileInput.disabled = isLoading;
    if (isLoading) {
        if(recommendationGrid) recommendationGrid.innerHTML = '';
        if(noRecommendationsText) noRecommendationsText.style.display = 'none';
        if(initialMessage) initialMessage.style.display = 'none';
    }
}

function applyDarkMode() { 
    if (isDarkMode) { document.body.classList.add('dark-mode'); if (darkModeIcon) darkModeIcon.textContent = '☀️'; } 
    else { document.body.classList.remove('dark-mode'); if (darkModeIcon) darkModeIcon.textContent = '🌙'; }
    localStorage.setItem('darkMode', isDarkMode);
}

async function fetchApi(endpoint, options = {}) { 
    if (!options._internalNoLoading) showLoading(true);
    let responseData = null;
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        responseData = await response.json();
        if (!response.ok) {
            console.error(`API Error (${response.status}) for ${endpoint}:`, responseData);
            alert(`Error: ${responseData.error || response.statusText || 'Unknown server error'}`);
            if (!options._internalNoLoading) showLoading(false);
            return null;
        }
        if (!options._internalNoLoading) showLoading(false);
        return responseData;
    } catch (error) {
        console.error(`Network/parsing error for ${endpoint}:`, error, "Response:", responseData);
        alert('Application error. Please check console.');
        if (!options._internalNoLoading) showLoading(false);
        return null;
    }
}

// --- Authentication ---
function updateUserAuthDisplay() { 
    if (!userAuthSection) return;
    if (loggedInUser && loggedInUser.username) {
        userAuthSection.innerHTML = `<span class="welcome-user">Welcome, ${loggedInUser.username}!</span><button id="logoutButton" class="btn-header-action btn-subtle">Logout</button>`;
        if(document.getElementById('logoutButton')) document.getElementById('logoutButton').addEventListener('click', handleLogout);
    } else {
        userAuthSection.innerHTML = `<button id="showLoginModalButton" class="btn-header-action">Login</button><button id="showSignupModalButton" class="btn-header-action">Sign Up</button>`;
        if(document.getElementById('showLoginModalButton')) document.getElementById('showLoginModalButton').addEventListener('click', () => { if(loginModal) loginModal.style.display = 'block'; });
        if(document.getElementById('showSignupModalButton')) document.getElementById('showSignupModalButton').addEventListener('click', () => { if(signupModal) signupModal.style.display = 'block'; });
    }
}
async function checkLoginStatus() { 
    const data = await fetchApi('/api/current_user_status', { _internalNoLoading: true });
    if (data && data.logged_in) {
        loggedInUser = data.user;
        wishlistItems = data.user.wishlist_details || await fetchUserWishlist(false); 
        cartItems = data.user.cart_details || await fetchUserCart(false);
    } else { loggedInUser = null; wishlistItems = []; cartItems = []; }
    updateUserAuthDisplay(); updateWishlistDisplay(); updateCartDisplay();
}
async function handleLogin(event) { 
    event.preventDefault(); const username = loginForm.loginUsername.value; const password = loginForm.loginPassword.value;
    const data = await fetchApi('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
    if (data && data.user) { alert(data.message); await checkLoginStatus(); if(loginModal) loginModal.style.display = 'none'; loginForm.reset(); } 
    else if (data && data.error) { alert(`Login Error: ${data.error}`); } else { alert("Login failed.");}
}
async function handleSignup(event) { 
    event.preventDefault(); const username = signupForm.signupUsername.value; const email = signupForm.signupEmail.value; const password = signupForm.signupPassword.value;
    const data = await fetchApi('/api/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, email, password }) });
    if (data && data.user) { alert(data.message); await checkLoginStatus(); if(signupModal) signupModal.style.display = 'none'; signupForm.reset(); } 
    else if (data && data.error) { alert(`Signup Error: ${data.error}`); } else { alert("Signup failed.");}
}
async function handleLogout() { 
    const data = await fetchApi('/api/logout');
    if (data) { alert(data.message); loggedInUser = null; wishlistItems = []; cartItems = []; await checkLoginStatus(); }
}

// --- User Data (Wishlist, Cart) ---
async function fetchUserWishlist(showLoader = true) {
    if (!loggedInUser) return [];
    const data = await fetchApi('/api/wishlist', showLoader ? {} : { _internalNoLoading: true });
    return data && Array.isArray(data.wishlist) ? data.wishlist : [];
}
async function fetchUserCart(showLoader = true) {
    if (!loggedInUser) return [];
    const data = await fetchApi('/api/cart', showLoader ? {} : { _internalNoLoading: true });
    return data && Array.isArray(data.cart) ? data.cart : [];
}

async function toggleWishlist(productId) {
    if (!loggedInUser) { alert("Login to manage wishlist."); if(loginModal)loginModal.style.display='block'; return; }
    const method = wishlistItems.some(item => item.id === productId) ? 'DELETE' : 'POST';
    const res = await fetchApi('/api/wishlist', { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ productId }) });
    if (res && res.wishlist_ids !== undefined) { 
        wishlistItems = await fetchUserWishlist(false); 
        updateWishlistDisplay();
        refreshCurrentRecommendationsDisplay(); 
    } else if (res && res.error) { alert(`Wishlist Error: ${res.error}`); }
}
async function toggleCart(productId) {
    if (!loggedInUser) { alert("Login to manage cart."); if(loginModal)loginModal.style.display='block'; return; }
    const method = cartItems.some(item => item.id === productId) ? 'DELETE' : 'POST';
    const res = await fetchApi('/api/cart', { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ productId }) });
    if (res && res.cart_items_data !== undefined) { 
        cartItems = await fetchUserCart(false); 
        updateCartDisplay();
        refreshCurrentRecommendationsDisplay(); 
        if (method === 'POST' && detailedProductToShow && detailedProductToShow.id === productId) closeModal();
    } else if (res && res.error) { alert(`Cart Error: ${res.error}`); }
}
async function updateUserPreference(action, value) {
    if (!loggedInUser) return;
    await fetchApi('/api/preferences/update', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,value})});
}

// --- Recommendations & AI Display ---
function renderProductCard(product) { 
    const isInCart = cartItems.some(item => item.id === product.id);
    const isInWishlist = wishlistItems.some(item => item.id === product.id);
    const card = document.createElement('div'); card.className = 'product-card'; card.dataset.productId = product.id;
    const wishlistHeartIcon = isInWishlist ? '💖' : '🤍';
    let cartBadgeHTML = isInCart ? `<div class="card-cart-status-badge" title="In Cart">🛒</div>` : '';
    let reasonHTML = product.recommendationReason ? `<p class="recommendation-reason">${product.recommendationReason}</p>` : '';
    const whyIconHTML = product.detailedReasons && product.detailedReasons.length > 0 ? `<span class="why-recommendation-icon" title="Details" style="cursor:help;">ℹ️</span>` : '';
    card.innerHTML = `<div class="card-actions-overlay">${cartBadgeHTML}<button class="card-wishlist-btn" data-product-id="${product.id}" title="${isInWishlist ? 'Remove from' : 'Add to'} Wishlist" aria-label="${isInWishlist ? 'Remove from' : 'Add to'} Wishlist">${wishlistHeartIcon}</button></div><div class="product-card-image-wrapper"><img src="${product.imageUrl || '#'}" alt="${product.name || 'Product'}"></div><div class="product-info"><div class="product-name-wrapper"><span class="product-name">${product.name || 'N/A'}</span>${whyIconHTML}</div><p class="product-price">${product.price || '$?.??'}</p>${product.type ? `<span class="product-type">${product.type}</span>` : ''}${reasonHTML}</div>`;
    card.addEventListener('click', (e) => { if (!e.target.closest('.card-wishlist-btn')) handleProductCardClick(product.id); });
    card.querySelector('.card-wishlist-btn').addEventListener('click', (e) => { e.stopPropagation(); toggleWishlist(product.id); });
    return card;
}

function displayRecommendations(products, isNewSearchResult = true) {
    if (isNewSearchResult) { 
        currentRecommendations = products || [];
    }
    const displayList = products || currentRecommendations; 

    if(recommendationGrid) recommendationGrid.innerHTML = '';
    if (displayList.length > 0) {
        displayList.forEach(product => {
            const cardElement = renderProductCard(product);
            if(recommendationGrid) recommendationGrid.appendChild(cardElement);
        });
        if(noRecommendationsText) noRecommendationsText.style.display = 'none';
    } else {
        if(noRecommendationsText && isNewSearchResult) noRecommendationsText.style.display = 'block';
    }
    if(initialMessage) initialMessage.style.display = 'none';
}

function refreshCurrentRecommendationsDisplay() {
    if (recommendationGrid && currentRecommendations.length > 0) {
        recommendationGrid.innerHTML = ''; 
        currentRecommendations.forEach(product => {
            const cardElement = renderProductCard(product);
            recommendationGrid.appendChild(cardElement);
        });
    } else if (recommendationGrid && currentRecommendations.length === 0) {
        const loadingEl = document.getElementById('loadingText');
        if(!loadingEl || loadingEl.style.display === 'none') {
            displayRecommendations([], true); 
        }
    }
    if (detailedProductToShow) updateModalButtons(detailedProductToShow.id);
}

function displayAiInsights(openaiDesc, geminiRefine) {
    let insightsVisible = false;
    const oaiEl = openaiDescriptionText; // Use declared const
    const geminiEl = geminiRefinementText; // Use declared const
    const insightsSectionEl = aiInsightsSection; // Use declared const

    if (oaiEl) {
        if (openaiDesc) { oaiEl.textContent = openaiDesc; insightsVisible = true; }
        else { oaiEl.textContent = 'N/A'; }
    }
    if (geminiEl) {
        if (geminiRefine) {
            let geminiStr = "";
            if (typeof geminiRefine === 'object' && geminiRefine !== null) {
                if (geminiRefine.error) { geminiStr = `Gemini Error: ${geminiRefine.error}\n`; if(geminiRefine.raw_text) geminiStr += `Raw: ${geminiRefine.raw_text}`; }
                else { 
                    if (geminiRefine.key_attributes) geminiStr += `Key Attributes:\n  - ${(Array.isArray(geminiRefine.key_attributes) ? geminiRefine.key_attributes.join('\n  - ') : geminiRefine.key_attributes)}\n\n`;
                    if (geminiRefine.refined_search_query) geminiStr += `Refined Query:\n  "${geminiRefine.refined_search_query}"\n\n`; // Corrected key
                    if (geminiRefine.complementary_item_categories) geminiStr += `Try with:\n  - ${(Array.isArray(geminiRefine.complementary_item_categories) ? geminiRefine.complementary_item_categories.join('\n  - ') : geminiRefine.complementary_item_categories)}\n\n`;
                    if (geminiRefine.user_intent_summary) geminiStr += `Summary:\n  ${geminiRefine.user_intent_summary}\n\n`;
                    if (geminiRefine.raw_text && geminiStr === "") geminiStr = `Raw Output:\n${geminiRefine.raw_text}`;
                }
            } else if (typeof geminiRefine === 'string') { geminiStr = geminiRefine; }
            else { geminiStr = "N/A or unexpected format."; }
            geminiEl.textContent = geminiStr.trim() || "No specific insights."; insightsVisible = true;
        } else { geminiEl.textContent = 'N/A'; }
    }
    if(insightsSectionEl) insightsSectionEl.style.display = insightsVisible ? 'block' : 'none';
}

async function fetchAndDisplayRecommendations(prompt = '', imageFileContext = null, isNewImageUpload = false) {
    const currentTextPromptValue = promptInput.value.trim() || prompt;
    let data;
    let formData = null;

    if (isNewImageUpload && imageFileContext) { // Scenario 1: New image uploaded
        console.log("JS: New image search. File:", imageFileContext.name, "Prompt:", currentTextPromptValue);
        currentUploadedFileObject = imageFileContext; // Set as current context
        formData = new FormData();
        formData.append('imageFile', imageFileContext);
        if (currentTextPromptValue) formData.append('prompt', currentTextPromptValue);
        data = await fetchApi('/upload_image', { method: 'POST', body: formData });
        if (data && data.image_preview_url) currentImagePreviewUrl = data.image_preview_url;

    } else if (!isNewImageUpload && currentUploadedFileObject) { // Scenario 2: Refining with prompt, using existing image
        console.log("JS: Refining existing image. File:", currentUploadedFileObject.name, "Prompt:", currentTextPromptValue);
        formData = new FormData();
        formData.append('imageFile', currentUploadedFileObject); // Re-send the current file
        formData.append('prompt', currentTextPromptValue);
        data = await fetchApi('/upload_image', { method: 'POST', body: formData });
        // Preview URL should remain the same or be updated by backend if it re-serves it

    } else { // Scenario 3: Text-only search
        console.log("JS: Text-only search. Prompt:", currentTextPromptValue);
        currentUploadedFileObject = null; // Clear image context
        currentImagePreviewUrl = null;
        if(imagePreview) imagePreview.style.display = 'none';
        if(imagePreviewPlaceholder) imagePreviewPlaceholder.style.display = 'block';
        data = await fetchApi('/get_recommendations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: currentTextPromptValue }) });
    }

    if (data) {
        displayRecommendations(data.recommendations, true); // New search results
        displayAiInsights(data.openai_description, data.gemini_refinement);
        if (data.image_preview_url && (isNewImageUpload || (currentUploadedFileObject && !imageFileContext))) { // If backend provided a preview URL
            if(imagePreview) { imagePreview.src = data.image_preview_url; imagePreview.style.display = 'block'; }
            if(imagePreviewPlaceholder) imagePreviewPlaceholder.style.display = 'none';
        }
    } else {
        displayRecommendations([], true);
        displayAiInsights(null, { error: "Failed to fetch recommendations." });
    }
}

// --- Image Upload & Prompt Submit ---
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => { if(imagePreview) imagePreview.src = e.target.result; }; // Client-side preview
        reader.readAsDataURL(file);
        fetchAndDisplayRecommendations(promptInput.value.trim(), file, true); // true for isNewImageUpload
    }
    if(imageFileInput) imageFileInput.value = null; // Reset for re-upload
}
function handlePromptSubmit(event) {
    event.preventDefault();
    const promptValue = promptInput.value.trim();
    // Pass currentUploadedFileObject as context if it exists.
    // isNewImageUpload is false, as this is a text prompt submission.
    fetchAndDisplayRecommendations(promptValue, null, false); 
}

// --- UI Update Functions (Wishlist, Cart, Modal etc.) ---
function findProductById(productId) { /* ... same ... */ 
    const recs = Array.isArray(currentRecommendations) ? currentRecommendations : []; const wish = Array.isArray(wishlistItems) ? wishlistItems : []; const cart = Array.isArray(cartItems) ? cartItems : [];
    return recs.find(p => p.id === productId) || wish.find(p => p.id === productId) || cart.find(p => p.id === productId) || (detailedProductToShow && detailedProductToShow.id === productId ? detailedProductToShow : null);
}
function updateWishlistDisplay() { /* ... same, but calls refreshCurrentRecommendationsDisplay at the end ... */
    if(!wishlistItemsList || !emptyWishlistMessage || !wishlistCount) return;
    wishlistItemsList.innerHTML = ''; emptyWishlistMessage.style.display = wishlistItems.length === 0 ? 'block' : 'none';
    wishlistItems.forEach(item => { 
        const li = document.createElement('li'); li.className = 'wishlist-item';
        li.innerHTML = `<img src="${item.imageUrl||'#'}" alt="${item.name||''}" class="wishlist-item-image"><div class="wishlist-item-details" data-product-id="${item.id}"><span class="wishlist-item-name">${item.name||'N/A'}</span><span class="wishlist-item-price">${item.price||'N/A'}</span></div><button class="wishlist-item-remove-btn btn-icon-subtle danger" data-product-id="${item.id}" title="Remove ${item.name||''}" aria-label="Remove ${item.name||''}"><span class="icon-placeholder-small">🗑️</span></button>`;
        const detailsDiv = li.querySelector('.wishlist-item-details'); li.querySelector('.wishlist-item-image').addEventListener('click', () => handleProductCardClick(item.id)); if(detailsDiv) detailsDiv.addEventListener('click', () => handleProductCardClick(item.id)); li.querySelector('.wishlist-item-remove-btn').addEventListener('click', (e) => { e.stopPropagation(); toggleWishlist(item.id); });
        wishlistItemsList.appendChild(li);
    });
    wishlistCount.textContent = wishlistItems.length;
    refreshCurrentRecommendationsDisplay(); // Refresh card icons
}
function updateCartDisplay() { /* ... same, but calls refreshCurrentRecommendationsDisplay at the end ... */
    if(!cartItemsList || !emptyCartMessage || !cartContents || !proceedToCheckoutBtn || !cartItemCount || !cartTotalPrice || !cartItemCountHeader) return;
    cartItemsList.innerHTML = ''; const isEmpty = cartItems.length === 0;
    emptyCartMessage.style.display = isEmpty ? 'block' : 'none'; cartContents.style.display = isEmpty ? 'none' : 'block'; proceedToCheckoutBtn.disabled = isEmpty;
    let currentTotal = 0;
    cartItems.forEach(item => { 
        const priceVal = parseFloat((item.price || '$0').replace('$', '')); if (!isNaN(priceVal)) currentTotal += (priceVal * (item.quantity || 1));
        const li = document.createElement('li'); li.className = 'cart-item';
        li.innerHTML = `<img src="${item.imageUrl||'#'}" alt="${item.name||''}" class="cart-item-image"><div class="cart-item-details" data-product-id="${item.id}"><span class="cart-item-name">${item.name||'N/A'}</span><span class="cart-item-price">${item.price||'N/A'} (Qty: ${item.quantity || 1})</span></div><button class="cart-item-remove-btn btn-icon-subtle danger" data-product-id="${item.id}" title="Remove ${item.name||''}" aria-label="Remove ${item.name||''}"><span class="icon-placeholder-small">🗑️</span></button>`;
        const detailsDiv = li.querySelector('.cart-item-details'); li.querySelector('.cart-item-image').addEventListener('click', () => handleProductCardClick(item.id)); if(detailsDiv) detailsDiv.addEventListener('click', () => handleProductCardClick(item.id)); li.querySelector('.cart-item-remove-btn').addEventListener('click', (e) => { e.stopPropagation(); toggleCart(item.id); });
        cartItemsList.appendChild(li);
    });
    const totalQty = cartItems.reduce((sum, item) => sum + (item.quantity || 1) ,0);
    cartItemCount.textContent = totalQty; cartItemCountHeader.textContent = totalQty;
    cartTotalPrice.textContent = currentTotal.toFixed(2);
    refreshCurrentRecommendationsDisplay(); // Refresh card icons
}
function updateModalButtons(productId) { /* ... same ... */ 
    if(!modalToggleWishlistBtn || !modalToggleCartBtn || !modalWishlistBtnText || !modalCartBtnText) return;
    const isInCart = cartItems.some(item => item.id === productId); const isInWishlist = wishlistItems.some(item => item.id === productId);
    modalWishlistBtnText.textContent = isInWishlist ? 'In Wishlist' : 'Add to Wishlist'; modalToggleWishlistBtn.querySelector('.icon-placeholder-small').textContent = isInWishlist ? '💖' : '🤍'; modalToggleWishlistBtn.classList.toggle('active', isInWishlist);
    modalCartBtnText.textContent = isInCart ? 'In Cart' : 'Add to Cart'; modalToggleCartBtn.classList.remove('add-to-cart-btn','remove-from-cart-btn'); modalToggleCartBtn.classList.add(isInCart ? 'remove-from-cart-btn' : 'add-to-cart-btn'); modalToggleCartBtn.querySelector('.icon-placeholder-small').textContent = isInCart ? '🛒' : '➕';
}
function handleProductCardClick(productId) { /* ... same, including preference logging ... */
    const product = findProductById(productId); if (!product) return; detailedProductToShow = product;
    if (loggedInUser) { if (product.category) updateUserPreference("interacted_category", product.category); if (product.color_tags && product.color_tags.length > 0) updateUserPreference("liked_color", product.color_tags[0]); }
    if(modalMainImage) modalMainImage.src = (product.images && product.images.length > 0 ? product.images[0] : product.imageUrl) || '#';
    if(modalProductName) modalProductName.textContent = product.name || 'N/A'; if(modalProductPrice) modalProductPrice.textContent = product.price || '$?.??'; if(modalProductDescription) modalProductDescription.textContent = product.description || "N/A";
    if(modalProductAttributes) { modalProductAttributes.innerHTML = ''; if (product.sizes && product.sizes.length) modalProductAttributes.innerHTML += `<p><strong>Sizes:</strong> ${product.sizes.join(', ')}</p>`; if (product.colors && product.colors.length) modalProductAttributes.innerHTML += `<p><strong>Colors:</strong> ${product.colors.join(', ')}</p>`; if (product.material) modalProductAttributes.innerHTML += `<p><strong>Material:</strong> ${product.material}</p>`; }
    if(modalRecommendationReason && modalReasonText && modalDetailedReasonsList) { if (product.recommendationReason || (product.detailedReasons && product.detailedReasons.length)) { modalRecommendationReason.style.display = 'block'; modalReasonText.textContent = product.recommendationReason || ""; modalDetailedReasonsList.innerHTML = ''; if (product.detailedReasons && product.detailedReasons.length) product.detailedReasons.forEach(r => {const li=document.createElement('li');li.textContent=r;modalDetailedReasonsList.appendChild(li);}); } else { modalRecommendationReason.style.display = 'none'; } }
    if(modalThumbnails) { modalThumbnails.innerHTML = ''; if (product.images && product.images.length > 1) product.images.forEach((url, i) => { const t=document.createElement('img');t.src=url;t.alt=`Thumb ${i+1}`;t.className=i===0?'active-thumbnail':'';t.onclick=()=>{if(modalMainImage)modalMainImage.src=url;modalThumbnails.querySelectorAll('img').forEach(th=>th.classList.remove('active-thumbnail'));t.classList.add('active-thumbnail');};modalThumbnails.appendChild(t); });}
    updateModalButtons(productId); if(productModalOverlay) productModalOverlay.style.display = 'flex';
}
function closeModal() { if(productModalOverlay) productModalOverlay.style.display = 'none'; detailedProductToShow = null; refreshCurrentRecommendationsDisplay(); /* Added to refresh card icons */ }

async function handleCheckout() { /* ... same ... */
    if (!loggedInUser) { alert("Login to checkout."); if(loginModal) loginModal.style.display='block'; return; }
    if (cartItems.length === 0) { alert("Cart is empty."); return; }
    const res = await fetchApi('/api/mock_checkout_process', { method: 'POST' });
    if (res && res.message) { alert(res.message + (res.orderId ? `\nID: ${res.orderId}` : "")); cartItems = await fetchUserCart(false); updateCartDisplay(); } 
    else if (res && res.error) { alert(`Checkout Error: ${res.error}`); } else { alert("Checkout failed."); }
}
function populateExamplePrompts() { /* ... same ... */ 
    if(!examplePromptsList) return; const examples = ["red summer dress", "formal black shoes", "men's casual shirt blue", "women's sports sneakers"]; examplePromptsList.innerHTML = '';
    examples.forEach(ex => {const li=document.createElement('li');li.textContent=ex;li.role='button';li.tabIndex=0;li.onclick=()=>{if(promptInput)promptInput.value=ex;if(clearPromptBtn)clearPromptBtn.style.display='inline-block';if(promptForm)promptForm.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));};li.onkeydown=(e)=>{if(e.key==='Enter'||e.key===' ')li.click();};examplePromptsList.appendChild(li);});
}

// --- Event Listeners & Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    if(closeLoginModalBtn) closeLoginModalBtn.addEventListener('click', () => { if(loginModal) loginModal.style.display='none'; });
    if(closeSignupModalBtn) closeSignupModalBtn.addEventListener('click', () => { if(signupModal) signupModal.style.display='none'; });
    if(switchToSignupBtn) switchToSignupBtn.addEventListener('click', (e) => { e.preventDefault(); if(loginModal) loginModal.style.display='none'; if(signupModal) signupModal.style.display='block'; });
    if(switchToLoginBtn) switchToLoginBtn.addEventListener('click', (e) => { e.preventDefault(); if(signupModal) signupModal.style.display='none'; if(loginModal) loginModal.style.display='block'; });
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (signupForm) signupForm.addEventListener('submit', handleSignup);
    if (darkModeToggle) darkModeToggle.addEventListener('click', () => { isDarkMode = !isDarkMode; applyDarkMode(); });
    if (imageFileInput) imageFileInput.addEventListener('change', handleImageUpload);
    if (promptForm) promptForm.addEventListener('submit', handlePromptSubmit);
    if (promptInput && clearPromptBtn) {
        promptInput.addEventListener('input', () => { if(clearPromptBtn) clearPromptBtn.style.display = promptInput.value ? 'inline-block' : 'none'; });
        clearPromptBtn.addEventListener('click', () => {
            if(promptInput) promptInput.value = ''; if(clearPromptBtn) clearPromptBtn.style.display = 'none'; 
            currentUploadedFileObject = null; currentImagePreviewUrl = null;
            if(imagePreview) imagePreview.style.display = 'none'; if(imagePreviewPlaceholder) imagePreviewPlaceholder.style.display = 'block';
            if(aiInsightsSection) aiInsightsSection.style.display = 'none';
            fetchAndDisplayRecommendations('', null, false); 
        });
    }
    if (productModalCloseBtn) productModalCloseBtn.addEventListener('click', closeModal);
    if (productModalOverlay) productModalOverlay.addEventListener('click', (e) => { if (e.target === productModalOverlay) closeModal(); });
    if (modalToggleWishlistBtn) modalToggleWishlistBtn.addEventListener('click', () => { if (detailedProductToShow) toggleWishlist(detailedProductToShow.id); });
    if (modalToggleCartBtn) modalToggleCartBtn.addEventListener('click', () => { if (detailedProductToShow) toggleCart(detailedProductToShow.id); });
    if (proceedToCheckoutBtn) proceedToCheckoutBtn.addEventListener('click', handleCheckout);

    applyDarkMode();
    const currentYearEl = document.getElementById('currentYear');
    if(currentYearEl) currentYearEl.textContent = new Date().getFullYear();
    
    await checkLoginStatus(); // Initial login check and data fetch

    if (!loggedInUser && typeof initialRecommendationsFromServer !== 'undefined' && initialRecommendationsFromServer.length > 0) {
        displayRecommendations(initialRecommendationsFromServer, true);
    } else if (!loggedInUser && (!initialRecommendationsFromServer || initialRecommendationsFromServer.length === 0)) {
       if(initialMessage) initialMessage.style.display = 'block';
    }
    populateExamplePrompts();
});