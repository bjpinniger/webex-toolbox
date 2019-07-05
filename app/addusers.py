from app.ciscowebex import add_users

def addusers(space_id, user_token, email_list):
    emails = []
    results = []
    for e in email_list:
        email = e.data['email_address']
        if len(email) > 0:
            result = add_users(user_token, email, space_id)
            emails.append(email)
            results.append(result)
    return emails, results
