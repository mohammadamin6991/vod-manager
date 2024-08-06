from rest_framework_simplejwt.backends import TokenBackend

def get_username(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    # data = {'token': token}
    try:
        valid_data = TokenBackend(algorithm='HS256').decode(token, verify=True)
        user = valid_data['user']
        request.user = user
    except Exception as v:
        print("validation error", v)
