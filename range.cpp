template <typename T, T min, T max> struct range {
  T val;

  T get_max() { return max; }
  T get_min() { return max; }

  operator T() const { return val; }
  template <T cmin, T cmax>
  operator range<T, cmin, cmax>() requires(cmin <= min and cmax >= max) { 
    return {val};
  }

  template <T rmin, T rmax>
  friend range<T, min + rmin, max + rmax>
  operator+(range<T, min, max> const &lhs, range<T, rmin, rmax> const &rhs) {
    return lhs.val + rhs.val;
  }

  template <T rmin, T rmax>
  friend range<T, min - rmin, max - rmax>
  operator-(range<T, min, max> const &lhs, range<T, rmin, rmax> const &rhs) {
    return lhs.val - rhs.val;
  }

  template <T rmin, T rmax>
  friend range<T, min * rmin, max * rmax>
  operator*(range<T, min, max> const &lhs, range<T, rmin, rmax> const &rhs) {
    return lhs.val * rhs.val;
  }

  template <T rmin, T rmax>
  friend range<T, min / rmin, max / rmax>
  operator/(range<T, min, max> const &lhs, range<T, rmin, rmax> const &rhs) {
    return lhs.val / rhs.val;
  }
};

