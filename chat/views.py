from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required


#@login_required
def chat_room(request, chat_id):
    ip_address = request.META.get('REMOTE_ADDR')
    return render(request, 'chat/room.html', {'chat_id': chat_id, 'ip_address': ip_address})
