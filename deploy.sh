git clone https://github.com/fandakrus/RAG-Food_export.git
sudo apt update
sudo apt install python3 python3-pip
sudo apt install python3-venv
cd RAG-Food_export/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
sudo apt install nginx
mv ~/deploy_config/chatbot.service /etc/systemd/system/chatbot.service
mv ~/deploy_config/user_manag.service /etc/systemd/system/user_manag.service
sudo systemctl start chatbot
sudo systemctl enable chatbot
sudo systemctl start user_manag
sudo systemctl enable user_manag
mv ~/deploy_config/nginx_config /etc/nginx/sites-available/myproject
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'