from rest_framework_simplejwt.tokens import RefreshToken

def generated_token(user):
    refresh = RefreshToken.for_user(user)      #token for every user 

    return {
        'refresh': str(refresh),
        'access' : str(refresh.access_token),
    }