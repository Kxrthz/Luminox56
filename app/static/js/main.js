// Luminox Confession Board - Complete JavaScript with Authentication

console.log('Luminox Confession Board loaded successfully!');

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initCharacterCounters();
    initFormHandlers();
    initModalHandlers();
    autoHideFlashMessages();
    addInteractiveEffects();
}

// Character counters for forms
function initCharacterCounters() {
    // Post content counter
    const postContent = document.getElementById('postContent');
    const charCount = document.getElementById('charCount');
    
    if (postContent && charCount) {
        postContent.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length;
            
            // Change color based on character count
            if (length > 900) {
                charCount.style.color = '#ef4444';
            } else if (length > 700) {
                charCount.style.color = '#f59e0b';
            } else {
                charCount.style.color = '#6b7280';
            }
        });
    }
    
    // Comment content counter
    const commentContent = document.getElementById('commentContent');
    const commentCharCount = document.getElementById('commentCharCount');
    
    if (commentContent && commentCharCount) {
        commentContent.addEventListener('input', function() {
            const length = this.value.length;
            commentCharCount.textContent = length;
            
            if (length > 450) {
                commentCharCount.style.color = '#ef4444';
            } else if (length > 350) {
                commentCharCount.style.color = '#f59e0b';
            } else {
                commentCharCount.style.color = '#6b7280';
            }
        });
    }
}

// Form submission handlers
function initFormHandlers() {
    // Post form
    const postForm = document.getElementById('postForm');
    if (postForm) {
        postForm.addEventListener('submit', handlePostSubmission);
    }
    
    // Comment form
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmission);
    }
}

// Modal event handlers
function initModalHandlers() {
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('postModal');
        if (event.target === modal) {
            hidePostModal();
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            hidePostModal();
        }
    });
}

// Auto-hide flash messages
function autoHideFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (alert && alert.parentElement) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
}

// Show post modal
function showPostModal() {
    const modal = document.getElementById('postModal');
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
        
        // Focus on textarea
        setTimeout(() => {
            const textarea = document.getElementById('postContent');
            if (textarea) textarea.focus();
        }, 100);
    }
}

// Hide post modal
function hidePostModal() {
    const modal = document.getElementById('postModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
        
        // Reset form
        const form = document.getElementById('postForm');
        if (form) {
            form.reset();
            const charCount = document.getElementById('charCount');
            if (charCount) {
                charCount.textContent = '0';
                charCount.style.color = '#6b7280';
            }
        }
    }
}

// Handle post submission
async function handlePostSubmission(event) {
    event.preventDefault();
    
    const content = document.getElementById('postContent').value.trim();
    const category = document.getElementById('postCategory').value;
    
    if (!content) {
        showAlert('Please write something before posting!', 'error');
        return;
    }
    
    if (content.length > 1000) {
        showAlert('Post is too long! Maximum 1000 characters.', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                category: category
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            hidePostModal();
            // Reload page to show new post
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error posting confession. Please try again.', 'error');
    } finally {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Handle comment submission
async function handleCommentSubmission(event) {
    event.preventDefault();
    
    const content = document.getElementById('commentContent').value.trim();
    const postId = document.getElementById('commentPostId').value;
    
    if (!content) {
        showAlert('Please write a comment before posting!', 'error');
        return;
    }
    
    if (content.length > 500) {
        showAlert('Comment is too long! Maximum 500 characters.', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                content: content
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Reset form
            document.getElementById('commentContent').value = '';
            const charCount = document.getElementById('commentCharCount');
            if (charCount) {
                charCount.textContent = '0';
                charCount.style.color = '#6b7280';
            }
            // Reload page to show new comment
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error adding comment. Please try again.', 'error');
    } finally {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Vote on posts
async function vote(postId, voteType) {
    try {
        const response = await fetch('/api/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                vote_type: voteType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update vote counts
            updateVoteCounts(postId, data, 'post');
            showAlert(`${voteType === 'up' ? 'Upvoted' : 'Downvoted'}!`, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error voting. Please try again.', 'error');
    }
}

// Vote on comments
async function voteComment(commentId, voteType) {
    try {
        const response = await fetch('/api/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                comment_id: commentId,
                vote_type: voteType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update comment vote counts
            updateVoteCounts(commentId, data, 'comment');
            showAlert(`Comment ${voteType === 'up' ? 'upvoted' : 'downvoted'}!`, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error voting. Please try again.', 'error');
    }
}

// Update vote counts on the page
function updateVoteCounts(id, data, type) {
    const prefix = type === 'comment' ? 'comment-' : '';
    
    // Update upvotes
    const upvoteElement = document.getElementById(`${prefix}upvotes-${id}`);
    if (upvoteElement) {
        upvoteElement.textContent = data.upvotes;
    }
    
    // Update downvotes
    const downvoteElement = document.getElementById(`${prefix}downvotes-${id}`);
    if (downvoteElement) {
        downvoteElement.textContent = data.downvotes;
    }
    
    // Update score
    const scoreElement = document.getElementById(`${prefix}score-${id}`);
    if (scoreElement) {
        scoreElement.textContent = data.score;
    }
}

// Add emoji reactions
async function addEmoji(postId, emoji) {
    try {
        const response = await fetch('/api/emoji', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                emoji: emoji
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Added ${emoji} reaction!`, 'success');
            // Could update reaction counts here if needed
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error adding reaction. Please try again.', 'error');
    }
}

// Show alert messages
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="alert-close">&times;</button>
    `;
    
    // Add to flash messages container
    const flashContainer = document.getElementById('flashMessages');
    if (flashContainer) {
        flashContainer.appendChild(alert);
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (alert && alert.parentElement) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 4000);
    }
}

// Add interactive effects
function addInteractiveEffects() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.post-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, .vote-btn, .emoji-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.3)';
            ripple.style.pointerEvents = 'none';
            ripple.style.transform = 'scale(0)';
            ripple.style.animation = 'ripple 0.6s linear';
            
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => {
                if (ripple.parentElement) {
                    ripple.remove();
                }
            }, 600);
        });
    });

    // Add hover effects to vote buttons
    const voteButtons = document.querySelectorAll('.vote-btn');
    voteButtons.forEach(btn => {
        if (btn.classList.contains('upvote')) {
            btn.addEventListener('mouseenter', function() {
                this.style.background = 'rgba(16, 185, 129, 0.2)';
                this.style.borderColor = '#10b981';
                this.style.color = '#10b981';
                this.style.transform = 'translateY(-2px)';
            });
            btn.addEventListener('mouseleave', function() {
                this.style.background = 'rgba(255, 255, 255, 0.1)';
                this.style.borderColor = '#374151';
                this.style.color = '#a1a1aa';
                this.style.transform = 'translateY(0)';
            });
        } else if (btn.classList.contains('downvote')) {
            btn.addEventListener('mouseenter', function() {
                this.style.background = 'rgba(239, 68, 68, 0.2)';
                this.style.borderColor = '#ef4444';
                this.style.color = '#ef4444';
                this.style.transform = 'translateY(-2px)';
            });
            btn.addEventListener('mouseleave', function() {
                this.style.background = 'rgba(255, 255, 255, 0.1)';
                this.style.borderColor = '#374151';
                this.style.color = '#a1a1aa';
                this.style.transform = 'translateY(0)';
            });
        }
    });

    // Add hover effects to emoji buttons
    const emojiButtons = document.querySelectorAll('.emoji-btn');
    emojiButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.transform = 'scale(1.2)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.transform = 'scale(1)';
        });
    });
}

// Utility functions
function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add CSS for ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .alert-info {
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid #3b82f6;
        color: #3b82f6;
    }
`;
document.head.appendChild(style);