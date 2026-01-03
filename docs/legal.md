# Legal Notice

This page contains important legal information regarding the use of the Handelsregister package.

## Usage Restrictions

!!! danger "Important: Rate Limits"

    It is **not permitted** to make more than **60 requests per hour** to the commercial register portal.
    
    The register portal is frequently targeted by automated mass queries, which often constitute criminal offenses under **§§ 303a, b StGB** (German Criminal Code - Computer Sabotage).

## Legal Basis

### Access Rights (§ 9 Abs. 1 HGB)

According to **§ 9 Abs. 1 HGB** (German Commercial Code), access to the commercial register is permitted to any person for informational purposes.

> "Die Einsichtnahme in das Handelsregister sowie in die zum Handelsregister eingereichten Dokumente ist jedem zu Informationszwecken gestattet."
>
> *Translation: Access to the commercial register and documents filed with it is permitted to everyone for informational purposes.*

### Data Protection (GDPR)

The data obtained from the commercial register may contain personal data. When using this data, you must comply with the **General Data Protection Regulation (GDPR)** and the **Bundesdatenschutzgesetz (BDSG)**.

In particular:

- Personal data may only be processed for legitimate purposes
- Data minimization principles apply
- Data subjects have rights regarding their data

---

## Terms of Use of handelsregister.de

The commercial register portal (handelsregister.de) has its own terms of use that must be observed:

1. **No mass queries** - Automated retrieval of large amounts of data is prohibited
2. **No commercial redistribution** - Data may not be resold or redistributed commercially without authorization
3. **Personal liability** - Users are personally responsible for their use of the portal

---

## Liability Disclaimer

### No Warranty

This package is provided "as is" without warranty of any kind. The authors and contributors:

- Do not guarantee the accuracy, completeness, or timeliness of data
- Are not liable for any damages resulting from use of this package
- Do not guarantee the availability or functionality of the package

### User Responsibility

Users of this package are responsible for:

- Complying with rate limits
- Observing applicable laws and regulations
- Proper handling of personal data
- Any consequences of their use

---

## Prohibited Uses

This package may **not** be used for:

1. **Mass data harvesting** - Systematic collection of all or large portions of register data
2. **Denial of Service** - Actions that could impair the portal's availability
3. **Commercial data resale** - Selling register data without authorization
4. **Stalking or harassment** - Using company or person data for harmful purposes
5. **Fraud** - Any fraudulent or deceptive purposes

---

## Best Practices

To use this package responsibly:

### Respect Rate Limits

```python
import time

# Wait between requests
for keyword in keywords:
    results = search(keyword)
    time.sleep(60)  # Max 60 requests per hour
```

### Use Caching

```python
# Caching is enabled by default
results = search("Bank")  # Fetched once, cached for 24h
```

### Minimize Requests

```python
# Good: Use server-side filtering
companies = search("Bank", states=["BE"], register_type="HRB")

# Bad: Fetch everything, filter locally
all_companies = search("Bank")  # Much larger response
filtered = [c for c in all_companies if c['state'] == 'BE']
```

---

## Reporting Issues

If you discover any issues with this package that could lead to misuse, please report them responsibly:

1. Open a GitHub issue (for non-security issues)
2. Contact the maintainers directly (for security issues)

---

## License

This package is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 BundesAPI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Contact

For questions regarding legal matters:

- **GitHub Issues**: [github.com/bundesAPI/handelsregister/issues](https://github.com/bundesAPI/handelsregister/issues)
- **BundesAPI**: [github.com/bundesAPI](https://github.com/bundesAPI)

