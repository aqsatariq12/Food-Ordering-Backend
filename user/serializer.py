from rest_framework import serializers
from user.models import User

class RegisterSerilizer(serializers.ModelSerializer):
    confirm_password  = serializers.CharField(style = {'input_type':'password'}, write_only=True)
    class Meta:
        model  = User
        fields = ['email','username','password','confirm_password','country','city']
        
        extra_kwargs = {
            'username':{'required':True},
            'password':{'write_only' :True},
            'email':{'required':True},
            'city':{'required':True},
            
        }

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        attrs['is_admin'] = False
        attrs['is_active'] = True

        if password != confirm_password:

            raise serializers.ValidationError({"password":"both passsword should be same. "})
        
        return attrs
    
    


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        model  = User
        fields = ['email', 'password']
    

class UserProfileSerializer(serializers.ModelSerializer):
   class Meta:
      model = User
      fields = ['id','email','username','city']