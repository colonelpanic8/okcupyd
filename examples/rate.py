"""Give a 5-star rating to 3 lucky 24-year-old straight/gay/bi women/men."""
import okcupyd

u = okcupyd.User()
profiles = u.search(location='minneapolis, mn', keywords='arrested development',
                    age_min=24, age_max=24)

for profile in profiles[:3]:
    profile.rate(5)
