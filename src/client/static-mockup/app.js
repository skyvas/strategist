// KAIRI & CO. - Core Storefront & Cart Engine
const FREE_SHIPPING_THRESHOLD = 50.00;

// Central Product Catalog
const CATALOG = {
  'classic-kairi': {
    id: 'classic-kairi',
    name: 'The Classic Kairi',
    category: 'Heritage Collection',
    price: 16.00,
    comparePrice: 19.00,
    image: 'images/classic_kairi.jpg',
    spiceLevel: 3,
    flavor: 'Tart, Mustardy, Fiery',
    desc: 'The undisputed king of Punjabi achar. Raw green mango steeped in cold-pressed mustard oil, fenugreek, and whole spices.'
  },
  'andhra-fire': {
    id: 'andhra-fire',
    name: 'Andhra Fire',
    category: 'Heritage Collection',
    price: 16.00,
    comparePrice: 19.00,
    image: 'images/andhra_fire.jpg',
    spiceLevel: 4,
    flavor: 'Smoky, Garlic, Deep Chili',
    desc: 'Fiery South Indian relish with slow-simmered vine tomatoes, whole roasted garlic, and crisp curry leaves.'
  },
  'hot-honey-mango': {
    id: 'hot-honey-mango',
    name: 'Hot Honey Mango',
    category: 'Studio Collection',
    price: 17.50,
    comparePrice: 21.00,
    image: 'images/hot_honey_mango.jpg',
    spiceLevel: 3,
    flavor: 'Sweet Heat, Ghost Pepper, Wildflower',
    desc: 'Sweet golden wildflower honey infused with tart raw mango and a subtle kiss of Bhut Jolokia (ghost pepper).'
  },
  'smoked-garlic': {
    id: 'smoked-garlic',
    name: 'Smoked Garlic & Chilli',
    category: 'Studio Collection',
    price: 17.50,
    comparePrice: 21.00,
    image: 'images/smoked_garlic.jpg',
    spiceLevel: 4,
    flavor: 'Crispy Garlic, Umami, Kashmiri Chili',
    desc: 'The Indian chili crisp. Whole roasted garlic cloves, crunchy seeds, and roasted Kashmiri chillies in infused oil.'
  },
  'tasting-box': {
    id: 'tasting-box',
    name: 'The Kairi Tasting Box (3-Pack)',
    category: 'Curated Bundles',
    price: 39.00,
    comparePrice: 48.00,
    image: 'images/tasting_box.jpg',
    spiceLevel: 3,
    flavor: '3 Best-Sellers + Brass Spoon',
    desc: 'The ultimate culinary gift set. Three artisanal jars and a handcrafted hammered brass tasting spoon.'
  },
  'tasting-spoon': {
    id: 'tasting-spoon',
    name: 'Handcrafted Brass Spoon',
    category: 'Accessories',
    price: 5.00,
    comparePrice: 8.00,
    image: 'images/tasting_box.jpg',
    spiceLevel: 0,
    flavor: 'Pure Hand-Forged Brass',
    desc: 'Traditional hammered brass tasting spoon for scooping achar.'
  }
};

// ==========================================
// KAIRI & CO. - CLIENT-SIDE TEMP DB ENGINE
// Multi-Tier Persistence: LocalStorage -> SessionStorage -> Web Cookies -> Memory
// ==========================================
const KairiTempDB = (function() {
  const memoryStore = {};

  // Cookie Read/Write Helpers
  function setCookie(name, value, days = 7) {
    try {
      let expires = "";
      if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
      }
      const serialized = encodeURIComponent(JSON.stringify(value));
      document.cookie = name + "=" + serialized + expires + "; path=/; SameSite=Lax";
    } catch (e) {
      // Cookies might be restricted in certain security contexts
    }
  }

  function getCookie(name) {
    try {
      const nameEQ = name + "=";
      const ca = document.cookie.split(';');
      for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) {
          const raw = decodeURIComponent(c.substring(nameEQ.length, c.length));
          return JSON.parse(raw);
        }
      }
    } catch (e) {
      // Fall through to null on parse errors
    }
    return null;
  }

  function deleteCookie(name) {
    try {
      document.cookie = name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; SameSite=Lax;';
    } catch (e) {}
  }

  // Multi-tier storage retriever
  function get(key, defaultValue = null) {
    // 1. Try LocalStorage
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const item = window.localStorage.getItem(key);
        if (item !== null) return JSON.parse(item);
      }
    } catch (e) {}

    // 2. Try SessionStorage
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        const sItem = window.sessionStorage.getItem(key);
        if (sItem !== null) return JSON.parse(sItem);
      }
    } catch (e) {}

    // 3. Try Web Cookies
    const cookieVal = getCookie(key);
    if (cookieVal !== null) return cookieVal;

    // 4. Try In-Memory Fallback
    if (memoryStore[key] !== undefined) {
      return memoryStore[key];
    }

    return defaultValue;
  }

  // Multi-tier storage setter
  function set(key, value) {
    memoryStore[key] = value;

    // LocalStorage
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, JSON.stringify(value));
      }
    } catch (e) {}

    // SessionStorage
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.setItem(key, JSON.stringify(value));
      }
    } catch (e) {}

    // Web Cookie Backup (for cart, session, orders)
    try {
      setCookie(key, value, 7);
    } catch (e) {}
  }

  function remove(key) {
    delete memoryStore[key];
    try {
      if (typeof window !== 'undefined' && window.localStorage) window.localStorage.removeItem(key);
    } catch (e) {}
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) window.sessionStorage.removeItem(key);
    } catch (e) {}
    deleteCookie(key);
  }

  // Client Session Initializer
  function initSession() {
    let session = get('kairi_session');
    if (!session) {
      session = {
        sessionId: 'kc_sess_' + Math.random().toString(36).substring(2, 9),
        startedAt: new Date().toISOString(),
        currency: 'CAD',
        region: 'Canada',
        device: /iPhone|iPad|iPod|Android/i.test(navigator.userAgent || '') ? 'mobile' : 'desktop'
      };
      set('kairi_session', session);
    }
    return session;
  }

  return {
    get,
    set,
    remove,
    setCookie,
    getCookie,
    initSession
  };
})();

// State Management (Backed by KairiTempDB with Local/Session/Cookie sync)
KairiTempDB.initSession();
let cart = KairiTempDB.get('kairi_cart', []);

function saveCart() {
  KairiTempDB.set('kairi_cart', cart);
  renderCartUI();
}

// Mobile Navigation Operations
function openMobileNav() {
  const drawer = document.getElementById('mobile-nav-drawer');
  const overlay = document.getElementById('mobile-nav-overlay');
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  if (drawer && overlay) {
    drawer.classList.add('active');
    overlay.classList.add('active');
    if (toggleBtn) {
      toggleBtn.classList.add('open');
      toggleBtn.setAttribute('aria-expanded', 'true');
    }
    document.body.style.overflow = 'hidden';
  }
}

function closeMobileNav() {
  const drawer = document.getElementById('mobile-nav-drawer');
  const overlay = document.getElementById('mobile-nav-overlay');
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  if (drawer && overlay) {
    drawer.classList.remove('active');
    overlay.classList.remove('active');
    if (toggleBtn) {
      toggleBtn.classList.remove('open');
      toggleBtn.setAttribute('aria-expanded', 'false');
    }
    document.body.style.overflow = '';
  }
}

function toggleMobileNav() {
  const drawer = document.getElementById('mobile-nav-drawer');
  if (drawer && drawer.classList.contains('active')) {
    closeMobileNav();
  } else {
    openMobileNav();
  }
}

// Cart Drawer Operations
function openCart() {
  closeMobileNav();
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-overlay');
  if (drawer && overlay) {
    drawer.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeCart() {
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-overlay');
  if (drawer && overlay) {
    drawer.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Add Item To Cart
function addToCart(productId, quantity = 1, variant = 'Single Jar (350g)', customPrice = null) {
  const product = CATALOG[productId];
  if (!product) return;

  const itemPrice = customPrice !== null ? customPrice : product.price;
  const existingIndex = cart.findIndex(item => item.id === productId && item.variant === variant);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({
      id: product.id,
      name: product.name,
      price: itemPrice,
      image: product.image,
      variant: variant,
      quantity: quantity
    });
  }

  saveCart();
  openCart();
}

// Update Item Quantity
function updateCartItemQty(index, change) {
  if (!cart[index]) return;
  cart[index].quantity += change;
  if (cart[index].quantity <= 0) {
    cart.splice(index, 1);
  }
  saveCart();
}

// Remove Item
function removeCartItem(index) {
  if (cart[index]) {
    cart.splice(index, 1);
    saveCart();
  }
}

// Render Cart UI
function renderCartUI() {
  const countBadges = document.querySelectorAll('.cart-badge');
  const cartBody = document.getElementById('cart-drawer-items');
  const subtotalEl = document.getElementById('cart-subtotal');
  const totalEl = document.getElementById('cart-total');
  const fillProgress = document.getElementById('shipping-fill');
  const shippingText = document.getElementById('shipping-msg');

  // Total count
  const totalItems = cart.reduce((acc, item) => acc + item.quantity, 0);
  countBadges.forEach(badge => badge.textContent = totalItems);

  // Subtotal
  const subtotal = cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)} CAD`;
  if (totalEl) totalEl.textContent = `$${subtotal.toFixed(2)} CAD`;

  // Free Shipping Calculation
  if (fillProgress && shippingText) {
    const progressPercent = Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100);
    fillProgress.style.width = `${progressPercent}%`;

    if (subtotal >= FREE_SHIPPING_THRESHOLD) {
      fillProgress.classList.add('unlocked');
      shippingText.innerHTML = '🎉 <strong>Congratulations!</strong> You unlocked Free Express Shipping in Canada!';
    } else {
      fillProgress.classList.remove('unlocked');
      const diff = (FREE_SHIPPING_THRESHOLD - subtotal).toFixed(2);
      shippingText.innerHTML = `Add <strong>$${diff} CAD</strong> more to unlock <strong>Free Shipping</strong>!`;
    }
  }

  // Items List
  if (cartBody) {
    if (cart.length === 0) {
      cartBody.innerHTML = `
        <div style="text-align: center; padding: 40px 10px; color: #888;">
          <div style="font-size: 40px; margin-bottom: 12px;">🏺</div>
          <p style="font-size: 16px; font-weight: 600; color: #181818; margin-bottom: 6px;">Your cart is empty</p>
          <p style="font-size: 13px; margin-bottom: 20px;">Stock your pantry with handcrafted Indian condiments.</p>
          <a href="product.html" class="btn btn-primary btn-small" onclick="closeCart()">Explore The Classic Kairi</a>
        </div>
      `;
    } else {
      cartBody.innerHTML = cart.map((item, idx) => `
        <div class="cart-item-row">
          <img src="${item.image}" alt="${item.name}" class="cart-item-thumb">
          <div class="cart-item-info">
            <h4 class="cart-item-title">${item.name}</h4>
            <div class="cart-item-variant">${item.variant}</div>
            <div class="cart-item-controls">
              <div class="qty-stepper">
                <button type="button" onclick="updateCartItemQty(${idx}, -1)" aria-label="Decrease quantity">−</button>
                <span>${item.quantity}</span>
                <button type="button" onclick="updateCartItemQty(${idx}, 1)" aria-label="Increase quantity">+</button>
              </div>
              <div class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</div>
            </div>
            <button type="button" class="cart-item-remove" onclick="removeCartItem(${idx})">Remove</button>
          </div>
        </div>
      `).join('');
    }
  }
}

// 1-Click Upsells in Cart
function addCartUpsell(productId) {
  addToCart(productId, 1, 'Standard');
}

// Simulated Checkout Modal
function launchCheckoutModal(paymentMethod = 'Standard') {
  if (cart.length === 0) {
    alert('Your cart is empty! Add some jars first.');
    return;
  }
  closeCart();
  const modal = document.getElementById('checkout-modal');
  const summaryEl = document.getElementById('checkout-modal-summary');
  if (modal && summaryEl) {
    const subtotal = cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
    const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : 9.99;
    const total = subtotal + shipping;

    summaryEl.innerHTML = `
      <div style="background: #FDFBF7; border: 1px solid #E8E2D6; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
        <h4 style="margin-bottom: 10px; font-size: 15px;">Order Summary (${cart.length} item types)</h4>
        ${cart.map(i => `
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px;">
            <span>${i.name} (x${i.quantity})</span>
            <span style="font-weight: 600;">$${(i.price * i.quantity).toFixed(2)} CAD</span>
          </div>
        `).join('')}
        <div style="border-top: 1px solid #E8E2D6; padding-top: 10px; margin-top: 10px; display: flex; justify-content: space-between; font-size: 13px;">
          <span>Shipping to Canada:</span>
          <span>${shipping === 0 ? '<strong style="color: #15803D;">FREE</strong>' : '$9.99 CAD'}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 16px; font-weight: 700; margin-top: 8px; color: #181818;">
          <span>Total:</span>
          <span>$${total.toFixed(2)} CAD</span>
        </div>
      </div>
      <div style="font-size: 13px; color: #666; margin-bottom: 20px;">
        <p><strong>Payment Method Selected:</strong> ${paymentMethod}</p>
        <p>🚀 Dispatched from Toronto Hub via Canada Post Expedited Parcel.</p>
      </div>
    `;
    modal.classList.add('active');
  }
}

function completeSimulatedOrder() {
  const orderNumber = `KC-${Math.floor(100000 + Math.random() * 900000)}`;
  const subtotal = cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : 9.99;
  const total = subtotal + shipping;

  // Persist completed order in Temp DB (Cookies / Sessions / LocalStorage)
  const existingOrders = KairiTempDB.get('kairi_orders', []);
  existingOrders.unshift({
    orderId: orderNumber,
    items: [...cart],
    subtotal: subtotal.toFixed(2),
    shipping: shipping.toFixed(2),
    total: total.toFixed(2),
    placedAt: new Date().toISOString(),
    status: 'Confirmed'
  });
  KairiTempDB.set('kairi_orders', existingOrders);

  cart = [];
  saveCart();
  const modalBody = document.getElementById('checkout-modal-body');
  if (modalBody) {
    modalBody.innerHTML = `
      <div style="text-align: center; padding: 30px 10px;">
        <div style="font-size: 48px; color: #15803D; margin-bottom: 16px;">✓</div>
        <h3 style="font-size: 26px; margin-bottom: 12px; font-family: var(--font-heading);">Order Confirmed!</h3>
        <p style="font-size: 15px; color: #666; margin-bottom: 10px;">Thank you for your order! Confirmation <strong>#${orderNumber}</strong></p>
        <p style="font-size: 13px; color: #888; margin-bottom: 24px;">Saved to session cookies & local mock DB. Fresh jars are being packed with love.</p>
        <button class="btn btn-primary" onclick="closeModal('checkout-modal')">Continue Browsing</button>
      </div>
    `;
  }
}

// Modal helper
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// "Find Your Achar" Flavor Quiz Engine
const QUIZ_QUESTIONS = [
  {
    question: "1. What is your heat tolerance?",
    options: [
      { text: "Mild & Tangy", desc: "Flavor over fire", key: "mild" },
      { text: "Pleasant Medium Kick", desc: "Warm spices that wake up the palate", key: "medium" },
      { text: "Fiery Obsession", desc: "Bring on the South Indian chillies", key: "hot" },
      { text: "Ghost Pepper Daredevil", desc: "Looking for sweet & wild heat", key: "fire" }
    ]
  },
  {
    question: "2. What are you putting it on first?",
    options: [
      { text: "Dal, Basmati Rice & Khichdi", desc: "Comfort classic dinners", key: "rice" },
      { text: "Sourdough Avocado Toast & Eggs", desc: "Elevated brunch staples", key: "toast" },
      { text: "Crispy Grilled Cheese / Burgers", desc: "Gooey melted cheese pairings", key: "cheese" },
      { text: "Grain Bowls & Roast Veggies", desc: "Clean, punchy meal prep", key: "bowls" }
    ]
  },
  {
    question: "3. What flavor profile calls your name?",
    options: [
      { text: "Tart Green Mango & Mustard Oil", desc: "Punjabi nostalgic perfection", key: "classic" },
      { text: "Sweet Honey meets Ghost Pepper", desc: "Trendy modern drizzle", key: "honey" },
      { text: "Smoky Roasted Garlic & Crunch", desc: "Chili crisp depth & umami", key: "garlic" },
      { text: "Sun-Dried Tomato & Curry Leaf", desc: "Fiery Andhra temple style", key: "andhra" }
    ]
  }
];

let quizCurrentStep = 0;
let quizAnswers = [];

function initQuiz() {
  quizCurrentStep = 0;
  quizAnswers = [];
  renderQuizStep();
}

function renderQuizStep() {
  const qContainer = document.getElementById('quiz-question-container');
  const rContainer = document.getElementById('quiz-result-container');
  const stepIndicators = document.querySelectorAll('.quiz-progress-step');

  if (!qContainer || !rContainer) return;

  stepIndicators.forEach((ind, i) => {
    ind.classList.toggle('active', i <= quizCurrentStep);
  });

  if (quizCurrentStep < QUIZ_QUESTIONS.length) {
    qContainer.style.display = 'block';
    rContainer.style.display = 'none';

    const cur = QUIZ_QUESTIONS[quizCurrentStep];
    qContainer.innerHTML = `
      <h3 class="quiz-question">${cur.question}</h3>
      <div class="quiz-options">
        ${cur.options.map((opt, idx) => `
          <button type="button" class="quiz-option-btn" onclick="selectQuizOption('${opt.key}')">
            <div class="quiz-option-title">${opt.text}</div>
            <div class="quiz-option-desc">${opt.desc}</div>
          </button>
        `).join('')}
      </div>
    `;
  } else {
    // Show Result
    qContainer.style.display = 'none';
    rContainer.style.display = 'block';

    let matchKey = 'classic-kairi';
    if (quizAnswers.includes('honey') || quizAnswers.includes('fire')) {
      matchKey = 'hot-honey-mango';
    } else if (quizAnswers.includes('garlic') || quizAnswers.includes('cheese')) {
      matchKey = 'smoked-garlic';
    } else if (quizAnswers.includes('hot') || quizAnswers.includes('andhra')) {
      matchKey = 'andhra-fire';
    }

    const matchedProduct = CATALOG[matchKey];
    rContainer.innerHTML = `
      <span class="section-eyebrow">YOUR PERFECT FLAVOR SOULMATE</span>
      <h3 style="font-size: 28px; margin-bottom: 8px;">Meet ${matchedProduct.name}</h3>
      <p style="color: #666; font-size: 14px; margin-bottom: 20px;">Based on your spice preferences and go-to meals, this jar is crafted for your palate.</p>
      <div class="quiz-result-card">
        <img src="${matchedProduct.image}" alt="${matchedProduct.name}">
        <div>
          <span class="product-tag ${matchedProduct.category.includes('Heritage') ? 'heritage' : 'studio'}">${matchedProduct.category}</span>
          <h4 style="font-size: 20px; margin: 6px 0;">${matchedProduct.name}</h4>
          <p style="font-size: 13px; color: #555; margin-bottom: 8px;"><strong>Flavor:</strong> ${matchedProduct.flavor}</p>
          <p style="font-size: 13px; color: #777; margin-bottom: 12px;">${matchedProduct.desc}</p>
          <div style="font-size: 18px; font-weight: 700; margin-bottom: 12px;">$${matchedProduct.price.toFixed(2)} CAD</div>
          <button class="btn btn-primary btn-small" onclick="addToCart('${matchedProduct.id}')">Add To My Cart</button>
        </div>
      </div>
      <button class="btn btn-secondary btn-small" onclick="initQuiz()">Retake Quiz</button>
    `;
  }
}

function selectQuizOption(key) {
  quizAnswers.push(key);
  quizCurrentStep++;
  renderQuizStep();
}

// 3-Pack Tasting Box Bundle Builder
let bundleSlots = [null, null, null];

function initBundleBuilder() {
  renderBundleUI();
}

function addJarToBundle(productId) {
  const emptyIndex = bundleSlots.findIndex(s => s === null);
  if (emptyIndex !== -1) {
    bundleSlots[emptyIndex] = productId;
    renderBundleUI();
  } else {
    alert("Your 3-Pack box is already full! Remove a jar first to swap.");
  }
}

function removeJarFromBundle(slotIndex) {
  bundleSlots[slotIndex] = null;
  renderBundleUI();
}

function renderBundleUI() {
  const slotsContainer = document.getElementById('bundle-slots');
  const countSpan = document.getElementById('bundle-count');
  const addBundleBtn = document.getElementById('add-bundle-btn');

  if (!slotsContainer) return;

  const filledCount = bundleSlots.filter(s => s !== null).length;
  if (countSpan) countSpan.textContent = `${filledCount}/3 Selected`;

  slotsContainer.innerHTML = bundleSlots.map((productId, idx) => {
    if (productId) {
      const prod = CATALOG[productId];
      return `
        <div class="bundle-slot filled">
          <button type="button" class="remove-slot-btn" onclick="removeJarFromBundle(${idx})" title="Remove">✕</button>
          <img src="${prod.image}" alt="${prod.name}">
          <div style="font-size: 11px; font-weight: 700; line-height: 1.2;">${prod.name}</div>
        </div>
      `;
    } else {
      return `
        <div class="bundle-slot">
          <span style="font-size: 24px; color: #C4B9A7; margin-bottom: 6px;">+</span>
          <span style="font-size: 12px; font-weight: 600; color: #8C8477;">Slot ${idx + 1}</span>
          <span style="font-size: 10px; color: #A0988A;">Click jar below</span>
        </div>
      `;
    }
  }).join('');

  if (addBundleBtn) {
    if (filledCount === 3) {
      addBundleBtn.disabled = false;
      addBundleBtn.innerHTML = 'Add Tasting Box to Cart ($39.00 CAD)';
      addBundleBtn.classList.remove('btn-secondary');
      addBundleBtn.classList.add('btn-primary');
    } else {
      addBundleBtn.disabled = true;
      addBundleBtn.innerHTML = `Select ${3 - filledCount} More Jars to Unlock Bundle`;
      addBundleBtn.classList.remove('btn-primary');
      addBundleBtn.classList.add('btn-secondary');
    }
  }
}

function addCompletedBundleToCart() {
  const names = bundleSlots.map(id => CATALOG[id]?.name).join(', ');
  addToCart('tasting-box', 1, `Custom 3-Pack (${names})`, 39.00);
}

// Recipe Modal Viewer
const RECIPES = {
  'grilled-cheese': {
    title: 'The Ultimate Spicy Achar Grilled Cheese',
    achar: 'Andhra Fire or The Classic Kairi',
    prepTime: '10 Mins',
    desc: 'Golden-crusted artisan sourdough with melted sharp cheddar, gruyere, and a generous smear of spicy mango achar. The acidity of the mango pickle cuts right through the rich cheese.',
    ingredients: [
      '2 thick slices sourdough bread',
      '2 tbsp unsalted butter (room temperature)',
      '1/2 cup sharp aged cheddar (grated)',
      '1/4 cup gruyere or fontina cheese',
      '1.5 tbsp Kairi & Co. Classic Kairi or Andhra Fire',
      'Pinch of sea salt'
    ],
    instructions: 'Spread butter on one side of each bread slice. On the unbuttered side of one slice, layer half the cheese, spoon over the achar evenly, and top with the remaining cheese. Cook in a preheated cast iron skillet over medium-low heat for 4-5 minutes per side until deeply golden and oozy.'
  },
  'avocado-toast': {
    title: 'Sunday Morning Achar Eggs & Avocado Toast',
    achar: 'Smoked Garlic & Chilli or Green Chilli Yuzu',
    prepTime: '8 Mins',
    desc: 'Crushed ripe avocado with flaky sea salt, fresh lemon juice, a soft-jammy boiled egg, and a spoonful of crisp chili-infused achar oil.',
    ingredients: [
      '1 thick slice country loaf (toasted)',
      '1 ripe Haas avocado',
      '1 pasture-raised egg (soft boiled 6.5 mins)',
      '1 tbsp Kairi & Co. Smoked Garlic & Chilli',
      'Fresh lemon juice, radish ribbons & sesame seeds'
    ],
    instructions: 'Mash avocado with lemon juice and salt. Spread generously over warm toasted sourdough. Slice the jammy egg in half and place on top. Spoon the crunchy smoked garlic achar over the egg yolk and avocado. Garnish with radish and sesame seeds.'
  }
};

function openRecipeModal(recipeKey) {
  const recipe = RECIPES[recipeKey];
  if (!recipe) return;

  const modal = document.getElementById('recipe-modal');
  const content = document.getElementById('recipe-modal-content');
  if (modal && content) {
    content.innerHTML = `
      <span class="section-eyebrow">HOW YOU #KAIRI RECIPES</span>
      <h3 style="font-size: 26px; margin: 8px 0 14px 0;">${recipe.title}</h3>
      <p style="font-size: 13px; color: #D97706; font-weight: 700; margin-bottom: 12px;">★ Best paired with: ${recipe.achar}</p>
      <p style="color: #666; font-size: 14px; margin-bottom: 20px;">${recipe.desc}</p>
      
      <h4 style="font-size: 15px; margin-bottom: 8px;">Ingredients</h4>
      <ul style="padding-left: 20px; font-size: 13px; color: #444; margin-bottom: 18px;">
        ${recipe.ingredients.map(ing => `<li style="margin-bottom: 4px;">${ing}</li>`).join('')}
      </ul>

      <h4 style="font-size: 15px; margin-bottom: 8px;">Preparation</h4>
      <p style="font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 24px;">${recipe.instructions}</p>
      
      <button class="btn btn-primary btn-small" onclick="closeModal('recipe-modal'); openCart();">Shop Condiments for this Recipe</button>
    `;
    modal.classList.add('active');
  }
}

// PDP Interactivity (Product Detail Page)
function initPDP() {
  const thumbs = document.querySelectorAll('.pdp-thumb-item');
  const mainImg = document.getElementById('pdp-main-img');
  
  if (thumbs.length && mainImg) {
    thumbs.forEach(thumb => {
      thumb.addEventListener('click', () => {
        thumbs.forEach(t => t.classList.remove('active'));
        thumb.classList.add('active');
        const newSrc = thumb.getAttribute('data-img');
        if (newSrc) mainImg.src = newSrc;
      });
    });
  }

  // Pack selector
  const packBtns = document.querySelectorAll('.pack-btn');
  const priceDisplay = document.getElementById('pdp-price-display');
  packBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      packBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      const price = btn.getAttribute('data-price');
      if (priceDisplay && price) {
        priceDisplay.textContent = `$${parseFloat(price).toFixed(2)} CAD`;
      }
    });
  });

  // Sticky Buy Bar scroll trigger
  const buyBox = document.querySelector('.pdp-buy-box');
  const stickyBar = document.getElementById('sticky-buy-bar');
  if (buyBox && stickyBar) {
    window.addEventListener('scroll', () => {
      const rect = buyBox.getBoundingClientRect();
      if (rect.bottom < 0) {
        stickyBar.classList.add('visible');
      } else {
        stickyBar.classList.remove('visible');
      }
    });
  }

  // Accordion toggles
  const accordionItems = document.querySelectorAll('.pdp-accordion-item');
  accordionItems.forEach(item => {
    const header = item.querySelector('.pdp-accordion-header');
    if (header) {
      header.addEventListener('click', () => {
        item.classList.toggle('open');
      });
    }
  });
}

// Newsletter Form Handler
function handleNewsletterSubmit(e) {
  e.preventDefault();
  const input = e.target.querySelector('input[type="email"]');
  if (input && input.value) {
    alert(`🎉 Welcome to the Kairi Club! Use code WELCOME10 for 10% off your first order.`);
    input.value = '';
  }
}

// Global DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  renderCartUI();

  // Desktop/Mobile Cart Triggers
  const cartIcon = document.getElementById('cart-icon-btn');
  const closeBtn = document.getElementById('close-cart-btn');
  const overlay = document.getElementById('cart-overlay');

  if (cartIcon) cartIcon.addEventListener('click', openCart);
  if (closeBtn) closeBtn.addEventListener('click', closeCart);
  if (overlay) overlay.addEventListener('click', closeCart);

  // Mobile Navigation Triggers
  const mobileToggle = document.getElementById('mobile-nav-toggle');
  const mobileClose = document.getElementById('mobile-nav-close');
  const mobileOverlay = document.getElementById('mobile-nav-overlay');

  if (mobileToggle) mobileToggle.addEventListener('click', toggleMobileNav);
  if (mobileClose) mobileClose.addEventListener('click', closeMobileNav);
  if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileNav);

  // Close mobile nav when clicking any nav link
  document.querySelectorAll('.mobile-nav-link').forEach(link => {
    link.addEventListener('click', closeMobileNav);
  });

  // Esc key closes modals and drawers
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCart();
      closeMobileNav();
      closeModal('checkout-modal');
      closeModal('recipe-modal');
    }
  });

  // Init Quiz if on page
  if (document.getElementById('quiz-question-container')) {
    initQuiz();
  }

  // Init Bundle Builder if on page
  if (document.getElementById('bundle-slots')) {
    initBundleBuilder();
  }

  // Init PDP if on page
  if (document.getElementById('pdp-main-img')) {
    initPDP();
  }

  // Newsletter
  const nlForms = document.querySelectorAll('.newsletter-form');
  nlForms.forEach(f => f.addEventListener('submit', handleNewsletterSubmit));
});
