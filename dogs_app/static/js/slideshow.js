/**
 * Full-featured slideshow component
 */

class Slideshow {
    constructor(photos) {
        this.photos = photos || [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.interval = null;
        this.timing = 5000;
        this.transition = 'fade';
        this.progressInterval = null;
        this.progressValue = 0;

        this.init();
    }

    init() {
        // Get DOM elements
        this.overlay = document.getElementById('slideshow-overlay');
        this.image = document.getElementById('slideshow-image');
        this.caption = document.getElementById('slideshow-caption');
        this.counter = document.getElementById('slideshow-counter');
        this.progressBar = document.getElementById('slideshow-progress-bar');
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.playIcon = document.getElementById('play-icon');
        this.pauseIcon = document.getElementById('pause-icon');
        this.timingSelect = document.getElementById('timing-select');
        this.transitionSelect = document.getElementById('transition-select');

        if (!this.overlay || this.photos.length === 0) return;

        this.bindEvents();
        this.preloadImages();
    }

    bindEvents() {
        // Start button
        const startBtn = document.getElementById('start-slideshow');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.start(0));
        }

        // Gallery items
        document.querySelectorAll('.gallery-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.start(index);
            });
        });

        // Navigation buttons
        document.getElementById('prev-btn')?.addEventListener('click', () => this.prev());
        document.getElementById('next-btn')?.addEventListener('click', () => this.next());
        document.getElementById('close-btn')?.addEventListener('click', () => this.close());
        this.playPauseBtn?.addEventListener('click', () => this.togglePlay());

        // Timing select
        this.timingSelect?.addEventListener('change', (e) => {
            this.timing = parseInt(e.target.value);
            if (this.isPlaying) {
                this.stopAutoPlay();
                this.startAutoPlay();
            }
        });

        // Transition select
        this.transitionSelect?.addEventListener('change', (e) => {
            this.transition = e.target.value;
        });

        // Keyboard controls
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Touch/swipe support
        this.initTouchEvents();
    }

    initTouchEvents() {
        let touchStartX = 0;
        let touchEndX = 0;

        this.overlay?.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        this.overlay?.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        }, { passive: true });
    }

    handleSwipe(startX, endX) {
        const threshold = 50;
        const diff = startX - endX;

        if (Math.abs(diff) > threshold) {
            if (diff > 0) {
                this.next();
            } else {
                this.prev();
            }
        }
    }

    handleKeyboard(e) {
        if (!this.overlay?.classList.contains('active')) return;

        switch (e.key) {
            case 'ArrowLeft':
                this.prev();
                break;
            case 'ArrowRight':
                this.next();
                break;
            case ' ':
                e.preventDefault();
                this.togglePlay();
                break;
            case 'Escape':
                this.close();
                break;
        }
    }

    preloadImages() {
        this.photos.forEach(photo => {
            const img = new Image();
            img.src = photo.url;
        });
    }

    start(index = 0) {
        this.currentIndex = index;
        this.overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        this.showImage();
        this.startAutoPlay();
    }

    close() {
        this.stopAutoPlay();
        this.overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    showImage() {
        const photo = this.photos[this.currentIndex];
        if (!photo) return;

        // Apply transition out
        if (this.transition === 'fade') {
            this.image.classList.add('fade-out');
        } else if (this.transition === 'slide') {
            this.image.classList.add('slide-out-left');
        }

        setTimeout(() => {
            this.image.src = photo.url;
            this.caption.textContent = photo.caption || '';
            if (photo.dogName) {
                this.caption.textContent += (photo.caption ? ' - ' : '') + photo.dogName;
            }
            this.counter.textContent = `${this.currentIndex + 1} / ${this.photos.length}`;

            // Remove transition classes
            this.image.classList.remove('fade-out', 'slide-out-left', 'slide-out-right');
        }, this.transition === 'none' ? 0 : 300);
    }

    next() {
        this.currentIndex = (this.currentIndex + 1) % this.photos.length;
        this.showImage();
        this.resetProgress();
    }

    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.photos.length) % this.photos.length;
        this.showImage();
        this.resetProgress();
    }

    togglePlay() {
        if (this.isPlaying) {
            this.stopAutoPlay();
        } else {
            this.startAutoPlay();
        }
    }

    startAutoPlay() {
        this.isPlaying = true;
        this.playIcon.style.display = 'none';
        this.pauseIcon.style.display = 'inline';

        this.resetProgress();
        this.interval = setInterval(() => this.next(), this.timing);

        // Progress bar animation
        this.startProgress();
    }

    stopAutoPlay() {
        this.isPlaying = false;
        this.playIcon.style.display = 'inline';
        this.pauseIcon.style.display = 'none';

        clearInterval(this.interval);
        this.interval = null;

        this.stopProgress();
    }

    startProgress() {
        this.progressValue = 0;
        this.progressBar.style.width = '0%';

        const step = 100 / (this.timing / 100);
        this.progressInterval = setInterval(() => {
            this.progressValue += step;
            this.progressBar.style.width = `${Math.min(this.progressValue, 100)}%`;
        }, 100);
    }

    stopProgress() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }

    resetProgress() {
        this.stopProgress();
        if (this.isPlaying) {
            this.startProgress();
        }
    }
}

// Initialize slideshow when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof slideshowPhotos !== 'undefined' && slideshowPhotos.length > 0) {
        window.slideshow = new Slideshow(slideshowPhotos);
    }
});
