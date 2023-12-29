css = '''
<style>
.chat-container {
    max-height: 500px;
    overflow-y: scroll;
}
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e;
    color: #fffafa;  /* Set the text color to cream or the desired color */
}
.chat-message.bot {
    background-color: #475063;
    color: #fffafa;  /* Set the text color to cream or the desired color */
}

.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://scontent-ham3-1.xx.fbcdn.net/v/t39.30808-6/302411566_467411905433126_4503192801209384300_n.png">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''